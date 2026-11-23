"""places_node: /map/find_nearest servisi (Gorev 5.2). Ayni saglayicilari kullanir.

    ros2 run map_tools places_node
    ros2 service call /map/find_nearest drone_interfaces/srv/FindNearest \
        "{tur: hastane, enlem: 39.9208, boylam: 32.8541, yaricap_m: 3000.0}"
    ros2 service call /map/find_nearest drone_interfaces/srv/FindNearest \
        "{ad: 'Anıtkabir', enlem: 39.92, boylam: 32.85}"
"""
from drone_interfaces.srv import FindNearest
import rclpy
from rclpy.node import Node

from .fabrika import saglayici_olustur
from .yer import HaritaHatasi


def sorgula(saglayici, tur, ad, enlem, boylam, yaricap_m):
    """ROS'suz cekirdek: (yer, hata). Servis cagrisi ve testler bunu kullanir."""
    try:
        if tur:
            yer = saglayici.en_yakin(tur, enlem, boylam, yaricap_m)
        elif ad:
            yer = saglayici.ara(ad, enlem, boylam, yaricap_m)
        else:
            return None, 'tur ya da ad verilmeli'
    except (HaritaHatasi, KeyError) as e:
        return None, str(e)
    return yer, '' if yer else f'{yaricap_m:g} m içinde bulunamadı'


class PlacesNode(Node):

    def __init__(self):
        super().__init__('places_node')
        p = self.declare_parameter
        self.saglayici = saglayici_olustur(p('saglayici', 'osm').value, float(p('zaman_asimi_s', 8.0).value),
                                           float(p('onbellek_s', 600.0).value))
        self.yaricap = float(p('arama_yaricapi_m', 3000.0).value)
        self.create_service(FindNearest, '/map/find_nearest', self._cagri)
        self.get_logger().info(f'/map/find_nearest hazır (sağlayıcı: {self.saglayici.ad})')

    def _cagri(self, istek, cevap):
        yer, hata = sorgula(self.saglayici, istek.tur, istek.ad, istek.enlem, istek.boylam,
                            istek.yaricap_m or self.yaricap)
        cevap.bulundu = yer is not None
        cevap.hata = hata
        if yer:
            cevap.yer_adi, cevap.enlem, cevap.boylam = yer.ad, yer.enlem, yer.boylam
            cevap.mesafe_m, cevap.kaynak = float(yer.mesafe_m), yer.kaynak
        return cevap


def main(args=None):
    rclpy.init(args=args)
    node = PlacesNode()
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
