"""PX4 ile konusan yardimci sinif: publisher/subscriber'lar, arm, mod, setpoint.

Tum PX4 ayrintilari burada toplanir; executor_node yalnizca bu sinifi kullanir.
"""
import math
import re

from px4_msgs.msg import (
    BatteryStatus, OffboardControlMode, TrajectorySetpoint, VehicleCommand,
    VehicleGlobalPosition, VehicleLandDetected, VehicleLocalPosition, VehicleStatus,
)
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from .planlayici import Poz

# PX4 topic'leri best-effort yayinlanir; varsayilan (reliable) QoS ile HIC veri gelmez.
PX4_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

NAN = float('nan')


class PX4Arayuz:
    """Bir rclpy Node'u uzerinden PX4 ile konusur.

    Yeni PX4 surumlerinde /fmu/out topic adlarinin sonunda _v1 gibi surum eki
    olabilir; bu sinif ROS grafigine bakip dogru adi kendisi bulur.
    """

    def __init__(self, node, on_ek='/fmu'):
        self.node = node
        self.on_ek = on_ek.rstrip('/')

        self._mod_pub = node.create_publisher(
            OffboardControlMode, f'{self.on_ek}/in/offboard_control_mode', PX4_QOS)
        self._hedef_pub = node.create_publisher(
            TrajectorySetpoint, f'{self.on_ek}/in/trajectory_setpoint', PX4_QOS)
        self._komut_pub = node.create_publisher(
            VehicleCommand, f'{self.on_ek}/in/vehicle_command', PX4_QOS)

        self.yerel = None      # VehicleLocalPosition
        self.global_ = None    # VehicleGlobalPosition
        self.durum = None      # VehicleStatus
        self.batarya = None    # BatteryStatus
        self.yer = None        # VehicleLandDetected

        self._bekleyen = {
            'vehicle_local_position': (VehicleLocalPosition, 'yerel'),
            'vehicle_global_position': (VehicleGlobalPosition, 'global_'),
            'vehicle_status': (VehicleStatus, 'durum'),
            'battery_status': (BatteryStatus, 'batarya'),
            'vehicle_land_detected': (VehicleLandDetected, 'yer'),
        }
        self._abonelikler = []
        self._uyari_sayaci = 0
        self._abone_ol()
        self._kesif_timer = node.create_timer(1.0, self._abone_ol)

    # -- topic kesfi --------------------------------------------------------
    def _abone_ol(self):
        if not self._bekleyen:
            self._kesif_timer.cancel()
            return
        adlar = [ad for ad, _ in self.node.get_topic_names_and_types()]
        for taban in list(self._bekleyen):
            desen = re.compile(rf'^{re.escape(self.on_ek)}/out/{taban}(_v(\d+))?$')
            bulunan = [(int(m.group(2) or 0), ad) for ad in adlar if (m := desen.match(ad))]
            if not bulunan:
                continue
            _, topic = max(bulunan)
            tip, alan = self._bekleyen.pop(taban)
            self._abonelikler.append(self.node.create_subscription(
                tip, topic, lambda msg, a=alan: setattr(self, a, msg), PX4_QOS))
            self.node.get_logger().info(f'PX4 abone: {topic}')
        if self._bekleyen:
            self._uyari_sayaci += 1
            if self._uyari_sayaci % 10 == 1:
                self.node.get_logger().warn(
                    f'PX4 topic bekleniyor: {", ".join(self._bekleyen)} '
                    '(MicroXRCEAgent ve PX4 SITL calisiyor mu?)')

    # -- zaman ---------------------------------------------------------------
    def zaman_us(self):
        return self.node.get_clock().now().nanoseconds // 1000

    # -- yayinlar --------------------------------------------------------------
    def kontrol_modu_yayinla(self, konum=True, hiz=False):
        msg = OffboardControlMode()
        msg.position = konum
        msg.velocity = hiz
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = self.zaman_us()
        self._mod_pub.publish(msg)

    def hedef_yayinla(self, x, y, z, yaw):
        msg = TrajectorySetpoint()
        msg.position = [float(x), float(y), float(z)]
        msg.velocity = [NAN, NAN, NAN]
        msg.acceleration = [NAN, NAN, NAN]
        msg.yaw = float(yaw)
        msg.timestamp = self.zaman_us()
        self._hedef_pub.publish(msg)

    def komut_gonder(self, komut, p1=0.0, p2=0.0, p3=0.0, p4=0.0, p5=0.0, p6=0.0, p7=0.0):
        msg = VehicleCommand()
        msg.command = komut
        msg.param1, msg.param2, msg.param3 = float(p1), float(p2), float(p3)
        msg.param4, msg.param5, msg.param6, msg.param7 = float(p4), float(p5), float(p6), float(p7)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = self.zaman_us()
        self._komut_pub.publish(msg)

    def arm(self):
        self.komut_gonder(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)

    def disarm(self):
        self.komut_gonder(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.0)

    def offboard_moduna_gec(self):
        # param1=1: custom mode, param2=6: PX4 OFFBOARD ana modu
        self.komut_gonder(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)

    def in_(self):
        self.komut_gonder(VehicleCommand.VEHICLE_CMD_NAV_LAND)

    def eve_don(self):
        self.komut_gonder(VehicleCommand.VEHICLE_CMD_NAV_RETURN_TO_LAUNCH)

    # -- okumalar ----------------------------------------------------------------
    @property
    def hazir(self):
        return self.yerel is not None and self.yerel.xy_valid and self.yerel.z_valid

    def poz(self):
        y = self.yerel
        yaw = y.heading if math.isfinite(y.heading) else 0.0
        return Poz(float(y.x), float(y.y), float(y.z), float(yaw))

    def hiz(self):
        y = self.yerel
        return math.sqrt(y.vx ** 2 + y.vy ** 2 + y.vz ** 2)

    @property
    def armli(self):
        return self.durum is not None and \
            self.durum.arming_state == VehicleStatus.ARMING_STATE_ARMED

    @property
    def offboardda(self):
        return self.durum is not None and \
            self.durum.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD

    @property
    def yerde(self):
        if self.yer is not None:
            return bool(self.yer.landed)
        return not self.armli

    @property
    def havada(self):
        return self.armli and not self.yerde

    @property
    def ref_latlon(self):
        y = self.yerel
        if y is None or not y.xy_global:
            return None
        return (float(y.ref_lat), float(y.ref_lon))

    @property
    def batarya_orani(self):
        b = self.batarya
        if b is None or not math.isfinite(b.remaining) or b.remaining < 0:
            return 1.0
        return float(b.remaining)
