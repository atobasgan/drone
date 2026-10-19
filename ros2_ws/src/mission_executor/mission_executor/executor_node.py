"""Gorev yurutucu: /drone/command dinler, drone'u PX4 offboard ile ucurur.

Tasarim (MIMARI.txt 3.9, KAVRAMLAR 5.2):
  - 20-50 Hz zamanlayici her tikte OffboardControlMode + mevcut hedefi yayinlar.
    Bu dongu HIC durmaz; yeni komut yalnizca hedef degiskenini gunceller.
  - Komutlar kuyrukta tutulur; biri bitince siradakine gecilir.
  - Her komut ve her liste once safety.Guvenlik'ten gecer.
"""
from collections import deque
import math

from drone_interfaces.msg import CommandList, Feedback
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import Empty

from . import mesajlar
from .geo import aci_sar
from .planlayici import Poz
from .px4_interface import PX4Arayuz
from .safety import AracDurumu, Guvenlik, Limitler, Reddedildi

BEKLEMEDE = 'BEKLEMEDE'
KALKIYOR = 'KALKIYOR'
HAVADA = 'HAVADA'
YURUTUYOR = 'YURUTUYOR'
INIYOR = 'INIYOR'

MSG_ALANLARI = ('komut', 'metre', 'derece', 'yon', 'enlem', 'boylam', 'tur', 'saniye', 'mps')


def msg_to_komut(adim):
    return {alan: getattr(adim, alan) for alan in MSG_ALANLARI}


class ExecutorNode(Node):

    def __init__(self):
        super().__init__('mission_executor')

        p = self.declare_parameter
        self.frekans = p('frekans_hz', 20.0).value
        self.varis_esigi = p('varis_esigi_m', 0.5).value
        self.varis_hiz_esigi = p('varis_hiz_esigi_mps', 0.3).value
        self.yaw_esigi = math.radians(p('yaw_esigi_derece', 5.0).value)
        self.isinma_tik = int(p('offboard_isinma_tik', 20).value)
        self.hiz_siniri = float(p('hiz_mps', 0.0).value)   # 0 = PX4 limitleri
        on_ek = p('px4_on_ek', '/fmu').value

        varsayilan = Limitler()
        limitler = Limitler(**{
            alan: float(p(alan, getattr(varsayilan, alan)).value)
            for alan in Limitler.__dataclass_fields__
        })
        self.guvenlik = Guvenlik(limitler)
        self.get_logger().info(f'Güvenlik limitleri: {limitler}')

        self.px4 = PX4Arayuz(self, on_ek)
        self.create_subscription(CommandList, '/drone/command', self._komut_cb, 10)
        self.create_subscription(Empty, '/drone/emergency_stop', self._acil_cb, 10)
        self.feedback_pub = self.create_publisher(Feedback, '/drone/feedback', 10)

        self.durum = BEKLEMEDE
        self.kuyruk = deque()
        self.aktif = None            # (komut sozlugu, Hedef)
        self.final = None            # aktif komutun hedef pozu
        self.setpoint = None         # yayinlanan (hiz sinirli) setpoint pozu
        self.isinma = 0
        self.bekle_bitis = None
        self._son_istek = 0          # offboard/arm isteklerini seyreltmek icin

        self.dt = 1.0 / self.frekans
        self.create_timer(self.dt, self._tik)
        self.get_logger().info(f'Yürütücü hazır ({self.frekans:g} Hz)')

    # ------------------------------------------------------------------ yardimci
    def _geri_bildir(self, durum, mesaj):
        self.feedback_pub.publish(Feedback(durum=durum, mesaj=mesaj))
        log = self.get_logger().warn if durum in ('reddedildi', 'hata') else self.get_logger().info
        log(f'[{durum}] {mesaj}')

    def _havada(self):
        return self.px4.havada or self.durum == KALKIYOR

    def _baz_poz(self):
        """Yeni komutun goreli hesaplanacagi poz: havada asili kalirken son hedef."""
        if self.final is not None and self.durum in (HAVADA, YURUTUYOR) and self.px4.offboardda:
            return self.final
        return self.px4.poz()

    def _arac_durumu(self, poz=None):
        return AracDurumu(
            poz=poz or self._baz_poz(),
            havada=self._havada(),
            batarya=self.px4.batarya_orani,
            ref_latlon=self.px4.ref_latlon,
        )

    def _yerinde_kal(self):
        """Hedefi mevcut konuma esitle (anlik fren) ve offboard'da tut."""
        poz = self.px4.poz()
        self.final = poz
        self.setpoint = poz
        if self.px4.armli and not self.px4.offboardda:
            self.px4.offboard_moduna_gec()

    def _iptal(self, sebep=None):
        self.kuyruk.clear()
        self.aktif = None
        self.bekle_bitis = None
        if self.px4.havada:
            self._yerinde_kal()
            self.durum = HAVADA
        elif self.durum != BEKLEMEDE:
            # Kalkis henuz yerden kesilmeden iptal edildi.
            self.setpoint = self.final = self.px4.poz()
            self.durum = BEKLEMEDE
        if sebep:
            self._geri_bildir('bilgi', sebep)

    # ------------------------------------------------------------------ callback
    def _komut_cb(self, msg):
        if not self.px4.hazir:
            self._geri_bildir('reddedildi', 'PX4 konum verisi henüz yok')
            return
        komutlar = [msg_to_komut(a) for a in msg.adimlar]
        if not komutlar:
            return
        self._gecikme_logla(msg)

        # "dur" her seyin onune gecer.
        if komutlar[0]['komut'] == 'dur' and len(komutlar) == 1:
            self._iptal()
            self._geri_bildir('tamamlandi', mesajlar.baslarken(komutlar[0]))
            return

        # Kalkis sirasinda gelen komut kalkisi iptal etmez, arkasina eklenir.
        ekle = msg.kuyruga_ekle or self.durum == KALKIYOR

        if ekle and (self.aktif or self.kuyruk):
            durum = self._arac_durumu()
            if self.aktif:
                durum = Guvenlik.sonraki_durum(durum, self.aktif[1])
            kontrol_listesi = list(self.kuyruk) + komutlar
            atla = len(self.kuyruk)
        else:
            durum = self._arac_durumu(self.px4.poz() if self.aktif else None)
            kontrol_listesi = komutlar
            atla = 0

        try:
            self.guvenlik.liste_kontrol_et(kontrol_listesi, durum)
        except Reddedildi as e:
            self._geri_bildir('reddedildi', str(e))
            return

        if not ekle:
            self._iptal()
        self.kuyruk.extend(kontrol_listesi[atla:])
        self._geri_bildir('kabul', f'{len(komutlar)} adım kabul edildi ({msg.kaynak or "?"})')
        if self.aktif is None:
            self._siradaki()

    def _acil_cb(self, _msg):
        self._iptal()
        self._geri_bildir('tamamlandi', 'ACİL DUR: kuyruk boşaltıldı, yerinde asılı kalıyorum')

    def _gecikme_logla(self, msg):
        t = msg.t_komut_hazir
        if t.sec == 0 and t.nanosec == 0:
            return
        gecikme = (self.get_clock().now() - Time.from_msg(t)).nanoseconds / 1e6
        self.get_logger().debug(f'parser -> executor: {gecikme:.1f} ms')

    # ------------------------------------------------------------------ yurutme
    def _siradaki(self):
        while self.kuyruk:
            komut = self.kuyruk.popleft()
            if self._baslat(komut):
                return
        self.aktif = None

    def _baslat(self, komut):
        """Komutu baslatir. Hemen biten komutlarda False dondurur (siradakine gecilir)."""
        try:
            hedef = self.guvenlik.kontrol_et(komut, self._arac_durumu())
        except Reddedildi as e:
            self._geri_bildir('reddedildi', str(e))
            self.kuyruk.clear()
            return False

        ad = komut['komut']
        self._geri_bildir('yurutuyor', mesajlar.baslarken(komut))

        if hedef.tip == 'hiz':
            self.hiz_siniri = hedef.mps
            return False
        if hedef.tip == 'dur':
            self._yerinde_kal()
            return False

        self.aktif = (komut, hedef)
        if hedef.tip == 'konum':
            if ad == 'kalk':
                self.setpoint = self.px4.poz()
                self.isinma = 0
                self.durum = KALKIYOR
            else:
                if not self.px4.offboardda:
                    self._yerinde_kal()
                self.durum = YURUTUYOR
            self.final = hedef.poz
        elif hedef.tip == 'bekle':
            self.bekle_bitis = self.get_clock().now().nanoseconds / 1e9 + hedef.saniye
            self.durum = YURUTUYOR
        elif hedef.tip == 'in':
            self.px4.in_()
            self.durum = INIYOR
        elif hedef.tip == 'eve_don':
            self.px4.eve_don()
            self.durum = INIYOR
        return True

    def _bitir(self):
        komut, _ = self.aktif
        self._geri_bildir('tamamlandi', f'{komut["komut"]} tamamlandı')
        self.aktif = None
        self.bekle_bitis = None
        if self.durum != BEKLEMEDE:
            self.durum = HAVADA
        self._siradaki()

    def _setpoint_ilerlet(self):
        """Hiz siniri varsa setpoint'i final'e dogru hiz*dt adimlarla tasir."""
        if self.final is None:
            return
        if self.setpoint is None or self.hiz_siniri <= 0:
            self.setpoint = self.final
            return
        s, f = self.setpoint, self.final
        d = (f.x - s.x, f.y - s.y, f.z - s.z)
        mesafe = math.sqrt(sum(v * v for v in d))
        adim = self.hiz_siniri * self.dt
        if mesafe <= adim:
            self.setpoint = f
        else:
            k = adim / mesafe
            self.setpoint = Poz(s.x + d[0] * k, s.y + d[1] * k, s.z + d[2] * k, f.yaw)

    def _vardi_mi(self):
        p, f = self.px4.poz(), self.final
        mesafe = math.dist((p.x, p.y, p.z), (f.x, f.y, f.z))
        yaw_hatasi = abs(aci_sar(p.yaw - f.yaw))
        return mesafe < self.varis_esigi and self.px4.hiz() < self.varis_hiz_esigi \
            and yaw_hatasi < self.yaw_esigi

    def _tik(self):
        if not self.px4.hazir:
            return
        if self.setpoint is None:
            self.setpoint = self.final = self.px4.poz()

        # 1) Akis: her tikte kontrol modu + setpoint (offboard'dan dusmemek icin)
        self._setpoint_ilerlet()
        sp = self.setpoint
        self.px4.kontrol_modu_yayinla(konum=True)
        self.px4.hedef_yayinla(sp.x, sp.y, sp.z, sp.yaw)

        # 2) Durum makinesi
        simdi = self.get_clock().now().nanoseconds / 1e9

        if self.durum == KALKIYOR:
            self.isinma += 1
            if self.isinma >= self.isinma_tik and simdi - self._son_istek > 1.0:
                if not self.px4.offboardda:
                    self.px4.offboard_moduna_gec()
                if not self.px4.armli:
                    self.px4.arm()
                self._son_istek = simdi
            if self.px4.armli and self.px4.offboardda and self._vardi_mi():
                self.durum = HAVADA
                self._bitir()

        elif self.durum == YURUTUYOR and self.aktif:
            _, hedef = self.aktif
            if hedef.tip == 'bekle':
                if simdi >= self.bekle_bitis:
                    self._bitir()
            elif self._vardi_mi():
                self._bitir()

        elif self.durum == INIYOR:
            if self.px4.yerde or not self.px4.armli:
                self.durum = BEKLEMEDE
                self.setpoint = self.final = self.px4.poz()
                if self.aktif:
                    self._bitir()

        elif self.durum == HAVADA and not self.px4.armli:
            # Ornegin QGC'den elle inildi ya da failsafe.
            self.durum = BEKLEMEDE
            self._iptal('drone artık arm değil; kuyruk temizlendi')


def main(args=None):
    rclpy.init(args=args)
    node = ExecutorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
