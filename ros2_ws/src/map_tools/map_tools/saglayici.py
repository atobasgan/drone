"""Harita saglayicisi arayuzu. Her saglayici iki soruya cevap verir:

    en_yakin(tur, enlem, boylam, yaricap_m) -> Yer | None   "en yakin hastane"   (Gorev 5.2)
    ara(ad, enlem, boylam, yaricap_m)       -> Yer | None   "Anıtkabir"          (Gorev 5.4)

None = aranan yaricapta yok. Ag hatasi, zaman asimi, gecersiz cevap -> HaritaHatasi.
Saglayicilar ayni arayuzu uyguladigi icin harita_node hangisini kullandigini bilmez
(parametre: saglayici = osm | google).
"""
from mission_executor.geo import haversine_m

from .yer import HaritaHatasi, Yer


class YerSaglayici:
    ad = 'temel'

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        raise NotImplementedError

    def ara(self, ad, enlem, boylam, yaricap_m):
        raise NotImplementedError


def en_yakini_sec(adaylar, enlem, boylam, kaynak):
    """[(ad, enlem, boylam), ...] -> mesafesi en kucuk Yer (bos liste -> None)."""
    yerler = [Yer(ad, e, b, haversine_m(enlem, boylam, e, b), kaynak) for ad, e, b in adaylar]
    return min(yerler, key=lambda y: y.mesafe_m) if yerler else None


def json_iste(oturum, yontem, url, zaman_asimi, **kw):
    """HTTP istegi; her hata HaritaHatasi'na cevrilir (node hicbir zaman cokmez)."""
    import requests
    try:
        yanit = getattr(oturum, yontem)(url, timeout=zaman_asimi, **kw)
        yanit.raise_for_status()
        return yanit.json()
    except requests.Timeout:
        raise HaritaHatasi(f'harita servisi {zaman_asimi:g} sn içinde cevap vermedi') from None
    except (requests.RequestException, ValueError) as e:
        raise HaritaHatasi(f'harita servisine ulaşılamadı ({type(e).__name__})') from None
