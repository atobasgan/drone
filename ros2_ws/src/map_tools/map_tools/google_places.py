"""Google Places API (New): ayni arayuzun ikinci uygulamasi (Gorev 5.4).

API anahtari KODDA ya da YAML'da DEGIL, ortam degiskeninde: GOOGLE_MAPS_API_KEY.
Google Cloud: proje -> "Places API (New)" etkinlestir -> anahtar olustur -> anahtari
yalnizca Places API ile sinirla.
"""
import os

from .saglayici import YerSaglayici, en_yakini_sec, json_iste
from .turler import tur_bilgisi
from .yer import HaritaHatasi

YAKIN_URL = 'https://places.googleapis.com/v1/places:searchNearby'
METIN_URL = 'https://places.googleapis.com/v1/places:searchText'
ALANLAR = 'places.displayName,places.location'


def google_adaylari(cevap):
    return [(p.get('displayName', {}).get('text', ''), p['location']['latitude'], p['location']['longitude'])
            for p in cevap.get('places', []) if 'location' in p]


class GooglePlacesSaglayici(YerSaglayici):
    ad = 'google'

    def __init__(self, anahtar=None, zaman_asimi=8.0, oturum=None):
        import requests
        self.anahtar = anahtar or os.environ.get('GOOGLE_MAPS_API_KEY', '')
        if not self.anahtar:
            raise HaritaHatasi('GOOGLE_MAPS_API_KEY ortam değişkeni yok')
        self.zaman_asimi = zaman_asimi
        self.oturum = oturum or requests.Session()

    def _iste(self, url, govde):
        basliklar = {'X-Goog-Api-Key': self.anahtar, 'X-Goog-FieldMask': ALANLAR}
        return json_iste(self.oturum, 'post', url, self.zaman_asimi, json=govde, headers=basliklar)

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        cevap = self._iste(YAKIN_URL, {
            'includedTypes': tur_bilgisi(tur)['google'], 'maxResultCount': 10, 'rankPreference': 'DISTANCE',
            'languageCode': 'tr',
            'locationRestriction': {'circle': {'center': {'latitude': enlem, 'longitude': boylam},
                                               'radius': float(min(yaricap_m, 50000))}},
        })
        return en_yakini_sec(google_adaylari(cevap), enlem, boylam, self.ad)

    def ara(self, ad, enlem, boylam, yaricap_m):
        cevap = self._iste(METIN_URL, {
            'textQuery': ad, 'maxResultCount': 5, 'languageCode': 'tr',
            'locationBias': {'circle': {'center': {'latitude': enlem, 'longitude': boylam},
                                        'radius': float(min(yaricap_m, 50000))}},
        })
        return en_yakini_sec(google_adaylari(cevap), enlem, boylam, self.ad)
