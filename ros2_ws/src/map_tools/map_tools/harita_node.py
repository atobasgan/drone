"""harita_node: parser ile yurutucu arasinda harita komutlarini cozer (Faz 5).

    parser ──/drone/command──> harita_node ──/drone/command_harita──> mission_executor
                                   │ yakin_yere_git / yere_git -> harita servisi (OSM | Google)
                                   │ -> [irtifaya_cik seyir] + git_koordinat
                                   └ diger komutlar beklemeden, AYNEN gecer

Yurutucunun kodu degismez: harita.launch.py onun girisini /drone/command_harita'ya baglar.
Kurallar:
  - "dur" ve /drone/emergency_stop HIC beklemez; bekleyen harita aramalarini iptal eder
    (arama 3 sn surerken "dur" denirse, gec gelen sonuc yurutulmez: nesil sayaci).
  - Siralama korunur: harita aramasi surerken gelen yeni komut onu sollamaz, arkasinda bekler.
  - Ag islemi ayri bir thread'de: ROS callback'leri bloklanmaz.
"""
import queue
import threading

from drone_interfaces.msg import CommandList, DroneCommand, Feedback
from mission_executor.geo import ned_to_enlem_boylam
from mission_executor.px4_interface import PX4Arayuz
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty

from .donustur import dur_mu, msg_to_adim, yeni_liste
from .fabrika import saglayici_olustur
from .yer_cozucu import Konum, YerCozucu


class HaritaNode(Node):

    def __init__(self, saglayici=None, thread=True):
        super().__init__('harita_node')
        p = self.declare_parameter
        saglayici = saglayici or saglayici_olustur(
            p('saglayici', 'osm').value, float(p('zaman_asimi_s', 8.0).value), float(p('onbellek_s', 600.0).value))
        self.cozucu = YerCozucu(
            saglayici,
            arama_yaricapi_m=float(p('arama_yaricapi_m', 3000.0).value),
            en_uzak_m=float(p('en_uzak_m', 1000.0).value),
            seyir_irtifasi_m=float(p('seyir_irtifasi_m', 30.0).value),
            git_koordinata_seyir=bool(p('git_koordinata_seyir', True).value),
        )
        self.varsayilan = (float(p('varsayilan_enlem', 39.9208).value), float(p('varsayilan_boylam', 32.8541).value))
        # Yalnizca konum OKUR (PX4Arayuz'un komut yayinlarini hic kullanmaz).
        self.px4 = PX4Arayuz(self, p('px4_on_ek', '/fmu').value)

        self.cikis = self.create_publisher(CommandList, p('cikis_topic', '/drone/command_harita').value, 10)
        self.feedback_pub = self.create_publisher(Feedback, '/drone/feedback', 10)
        self.create_subscription(CommandList, p('giris_topic', '/drone/command').value, self._komut_cb, 10)
        self.create_subscription(Empty, '/drone/emergency_stop', self._acil_cb, 10)

        self._kilit = threading.Lock()
        self._kuyruk = queue.Queue()
        self._bekleyen = 0           # kuyrukta ya da islenmekte olan liste sayisi
        self._nesil = 0              # her dur / ACIL DUR'da artar
        if thread:
            threading.Thread(target=self._isci, daemon=True).start()
        self.get_logger().info(f'harita_node hazır: sağlayıcı {self.cozucu.saglayici.ad}, '
                               f'seyir {self.cozucu.seyir_irtifasi_m:g} m, en uzak {self.cozucu.en_uzak_m:g} m')

    # ------------------------------------------------------------------ giris
    def _komut_cb(self, msg):
        if dur_mu(msg):                              # dur beklemez, bekleyenleri iptal eder
            self._iptal_et('dur geldi')
            self.cikis.publish(msg)
            return
        adimlar = [msg_to_adim(a) for a in msg.adimlar]
        with self._kilit:
            if self._bekleyen == 0 and not self.cozucu.gerekli_mi(adimlar):
                self.cikis.publish(msg)              # harita isi yok: gecikme eklenmez
                return
            self._bekleyen += 1
            self._kuyruk.put((self._nesil, msg, adimlar))

    def _acil_cb(self, _msg):
        self._iptal_et('ACİL DUR')

    def _iptal_et(self, sebep):
        with self._kilit:
            self._nesil += 1
            atilan = 0
            while not self._kuyruk.empty():
                self._kuyruk.get_nowait()
                self._bekleyen -= 1
                atilan += 1
        if atilan:
            self._geri_bildir('reddedildi', f'{sebep}: bekleyen {atilan} harita komutu iptal edildi')

    # ------------------------------------------------------------------ isleme
    def _isci(self):
        while True:
            self.isle(*self._kuyruk.get())

    def isle(self, nesil, msg, adimlar):
        """Kuyruktaki bir listeyi cozer ve yayinlar (testlerde dogrudan cagrilir)."""
        try:
            sonuc = self.cozucu.coz(adimlar, self.konum()) if self.cozucu.gerekli_mi(adimlar) else None
            with self._kilit:
                if nesil != self._nesil:             # arama surerken dur geldi: sonucu at
                    self._geri_bildir('reddedildi', f'"{msg.metin}" dur geldiği için iptal edildi')
                    return
                if sonuc is not None and not sonuc.basarili:
                    self._geri_bildir('reddedildi', sonuc.hata)
                    return
                for mesaj in (sonuc.mesajlar if sonuc else []):
                    self._geri_bildir('bilgi', mesaj)
                self.cikis.publish(yeni_liste(msg, sonuc.adimlar, CommandList, DroneCommand) if sonuc else msg)
        except Exception as e:                      # node asla cokmemeli
            self.get_logger().error(f'harita komutu işlenemedi: {e}')
            self._geri_bildir('hata', f'harita komutu işlenemedi: {e}')
        finally:
            with self._kilit:
                self._bekleyen -= 1

    def konum(self):
        """Drone'un enlem/boylam/irtifasi; yurutucuyle ayni cerceve (yerel NED + PX4 referansi)."""
        if self.px4.hazir and self.px4.ref_latlon:
            poz = self.px4.poz()
            enlem, boylam = ned_to_enlem_boylam(poz.x, poz.y, *self.px4.ref_latlon)
            return Konum(enlem, boylam, irtifa_m=poz.irtifa)
        irtifa = self.px4.poz().irtifa if self.px4.hazir else None
        return Konum(*self.varsayilan, irtifa_m=irtifa, gps=False)

    def _geri_bildir(self, durum, mesaj):
        self.feedback_pub.publish(Feedback(durum=durum, mesaj=mesaj))
        self.get_logger().info(f'[{durum}] {mesaj}')


def main(args=None):
    rclpy.init(args=args)
    node = HaritaNode()
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
