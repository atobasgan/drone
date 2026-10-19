"""Gorev 1.3 test node'u: PX4'ten gelen konumu/durumu saniyede bir yazdirir.

    ros2 run mission_executor konum_izleyici
Drone'u QGC'den ucururken degerlerin degistigini gormelisin.
"""
import math

import rclpy
from rclpy.node import Node

from .px4_interface import PX4Arayuz


class KonumIzleyici(Node):
    def __init__(self):
        super().__init__('konum_izleyici')
        self.px4 = PX4Arayuz(self)
        self.create_timer(1.0, self._yaz)

    def _yaz(self):
        if not self.px4.hazir:
            self.get_logger().info('konum verisi bekleniyor...')
            return
        p = self.px4.poz()
        g = self.px4.global_
        konum = f'enlem={g.lat:.6f} boylam={g.lon:.6f} ' if g is not None else ''
        self.get_logger().info(
            f'NED x={p.x:7.2f} y={p.y:7.2f} z={p.z:7.2f} (irtifa {p.irtifa:6.2f} m) '
            f'yaw={math.degrees(p.yaw):6.1f}° hiz={self.px4.hiz():4.2f} m/s {konum}'
            f'arm={self.px4.armli} offboard={self.px4.offboardda} yerde={self.px4.yerde} '
            f'batarya=%{self.px4.batarya_orani * 100:.0f}')


def main(args=None):
    rclpy.init(args=args)
    node = KonumIzleyici()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
