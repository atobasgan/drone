"""OpenStreetMap: ucretsiz, anahtar gerekmez (Gorev 5.2).

  Overpass  : "su noktanin X metre cevresindeki hastaneler"  -> en_yakin
  Nominatim : "Anıtkabir"  -> koordinat                       -> ara
Kullanim kurallari: Nominatim saniyede en fazla 1 istek ve tanimlayici User-Agent ister.
Drone komutu icin bu siklik fazlasiyla yeterli.
"""
from .saglayici import YerSaglayici, en_yakini_sec, json_iste
from .turler import tur_bilgisi

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
KULLANICI = 'llm-drone/0.5 (Turkce sesli komutla drone kontrolu, egitim projesi)'


def overpass_sorgusu(etiketler, enlem, boylam, yaricap_m, zaman_asimi):
    """amenity=hospital -> nwr(around:R,lat,lon)["amenity"="hospital"]; out center;"""
    parcalar = []
    for etiket in etiketler:
        anahtar, deger = etiket.split('=')
        parcalar.append(f'nwr(around:{int(yaricap_m)},{enlem},{boylam})["{anahtar}"="{deger}"];')
    return f'[out:json][timeout:{int(zaman_asimi)}];({"".join(parcalar)});out center tags 50;'


def overpass_adaylari(cevap):
    """Dugum (node) koordinati dogrudan, yol/iliski (way/relation) icin "center" kullanilir."""
    adaylar = []
    for e in cevap.get('elements', []):
        konum = e if 'lat' in e else e.get('center')
        if not konum:
            continue
        etiket = e.get('tags', {})
        adaylar.append((etiket.get('name:tr') or etiket.get('name') or '', konum['lat'], konum['lon']))
    return adaylar


class OSMSaglayici(YerSaglayici):
    ad = 'osm'

    def __init__(self, zaman_asimi=8.0, oturum=None):
        import requests
        self.zaman_asimi = zaman_asimi
        self.oturum = oturum or requests.Session()
        self.oturum.headers.update({'User-Agent': KULLANICI})

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        sorgu = overpass_sorgusu(tur_bilgisi(tur)['osm'], enlem, boylam, yaricap_m, self.zaman_asimi)
        cevap = json_iste(self.oturum, 'post', OVERPASS_URL, self.zaman_asimi + 2, data={'data': sorgu})
        yer = en_yakini_sec(overpass_adaylari(cevap), enlem, boylam, self.ad)
        if yer and not yer.ad:
            yer.ad = tur_bilgisi(tur)['ad']
        return yer

    def ara(self, ad, enlem, boylam, yaricap_m):
        # viewbox: aramayi drone'un cevresine yonlendir (yaklasik derece; 1 derece ~ 111 km)
        d = yaricap_m / 111000.0
        parametre = {'q': ad, 'format': 'jsonv2', 'limit': 5, 'accept-language': 'tr', 'bounded': 1,
                     'viewbox': f'{boylam - d},{enlem + d},{boylam + d},{enlem - d}'}
        cevap = json_iste(self.oturum, 'get', NOMINATIM_URL, self.zaman_asimi, params=parametre)
        adaylar = [(r.get('name') or r.get('display_name', ad).split(',')[0], float(r['lat']), float(r['lon']))
                   for r in cevap]
        return en_yakini_sec(adaylar, enlem, boylam, self.ad)
