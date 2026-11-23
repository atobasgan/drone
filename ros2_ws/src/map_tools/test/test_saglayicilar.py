"""OSM ve Google saglayicilari: ag yok, belgelenmis cevap bicimleriyle sahte HTTP."""
import pytest
import requests

from map_tools.fabrika import saglayici_olustur
from map_tools.google_places import GooglePlacesSaglayici
from map_tools.osm import OSMSaglayici, overpass_adaylari, overpass_sorgusu
from map_tools.yer import HaritaHatasi


class Yanit:
    def __init__(self, veri, kod=200):
        self.veri, self.status_code = veri, kod

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f'{self.status_code}')

    def json(self):
        return self.veri


class Oturum:
    def __init__(self, cevap=None, hata=None):
        self.cevap, self.hata, self.istekler, self.headers = cevap, hata, [], {}

    def _iste(self, yontem, url, **kw):
        self.istekler.append((yontem, url, kw))
        if self.hata:
            raise self.hata
        return self.cevap

    def post(self, url, **kw):
        return self._iste('post', url, **kw)

    def get(self, url, **kw):
        return self._iste('get', url, **kw)


OVERPASS = {'elements': [
    {'type': 'node', 'lat': 39.9300, 'lon': 32.8600, 'tags': {'amenity': 'hospital', 'name': 'Uzak Hastane'}},
    {'type': 'way', 'center': {'lat': 39.9220, 'lon': 32.8550},
     'tags': {'amenity': 'hospital', 'name': 'Yakın Hastane'}},
    {'type': 'way', 'tags': {'name': 'konumsuz'}},
]}


def test_overpass_sorgusu_ve_ayristirma():
    q = overpass_sorgusu(['shop=supermarket', 'shop=convenience'], 39.92, 32.85, 3000, 8)
    assert 'nwr(around:3000,39.92,32.85)["shop"="supermarket"];' in q and '"convenience"' in q
    assert [a[0] for a in overpass_adaylari(OVERPASS)] == ['Uzak Hastane', 'Yakın Hastane']


def test_osm_en_yakin_ve_ara():
    o = Oturum(Yanit(OVERPASS))
    yer = OSMSaglayici(oturum=o).en_yakin('hastane', 39.9208, 32.8541, 3000)
    assert yer.ad == 'Yakın Hastane' and yer.kaynak == 'osm' and yer.mesafe_m < 200
    assert o.istekler[0][0] == 'post' and 'amenity' in o.istekler[0][2]['data']['data']
    assert 'User-Agent' in o.headers                                   # Nominatim kurali
    nominatim = [{'name': 'Anıtkabir', 'lat': '39.9255', 'lon': '32.8369', 'display_name': 'Anıtkabir, Ankara'}]
    o = Oturum(Yanit(nominatim))
    yer = OSMSaglayici(oturum=o).ara('Anıtkabir', 39.9208, 32.8541, 3000)
    assert yer.ad == 'Anıtkabir' and 1000 < yer.mesafe_m < 2500
    assert o.istekler[0][2]['params']['q'] == 'Anıtkabir'


def test_isimsiz_yere_tur_adi_verilir_ve_bos_sonuc():
    isimsiz = {'elements': [{'type': 'node', 'lat': 39.921, 'lon': 32.855, 'tags': {'amenity': 'pharmacy'}}]}
    assert OSMSaglayici(oturum=Oturum(Yanit(isimsiz))).en_yakin('eczane', 39.92, 32.85, 500).ad == 'eczane'
    assert OSMSaglayici(oturum=Oturum(Yanit({'elements': []}))).en_yakin('eczane', 39.92, 32.85, 500) is None


@pytest.mark.parametrize('hata, mesaj', [(requests.Timeout(), 'cevap vermedi'),
                                         (requests.ConnectionError(), 'ulaşılamadı')])
def test_ag_hatasi_harita_hatasina_cevrilir(hata, mesaj):
    with pytest.raises(HaritaHatasi, match=mesaj):
        OSMSaglayici(oturum=Oturum(hata=hata)).en_yakin('park', 39.92, 32.85, 1000)
    with pytest.raises(HaritaHatasi):
        OSMSaglayici(oturum=Oturum(Yanit({}, 429))).en_yakin('park', 39.92, 32.85, 1000)


def test_google_places_istek_ve_cevap():
    cevap = {'places': [{'displayName': {'text': 'Opet'}, 'location': {'latitude': 39.925, 'longitude': 32.858}},
                        {'displayName': {'text': 'Shell'}, 'location': {'latitude': 39.95, 'longitude': 32.90}}]}
    o = Oturum(Yanit(cevap))
    yer = GooglePlacesSaglayici(anahtar='TEST', oturum=o).en_yakin('benzinlik', 39.9208, 32.8541, 3000)
    assert yer.ad == 'Opet' and yer.kaynak == 'google'
    _, url, kw = o.istekler[0]
    assert url.endswith(':searchNearby') and kw['headers']['X-Goog-Api-Key'] == 'TEST'
    assert kw['json']['includedTypes'] == ['gas_station'] and kw['json']['rankPreference'] == 'DISTANCE'
    o = Oturum(Yanit({'places': []}))
    assert GooglePlacesSaglayici(anahtar='T', oturum=o).ara('Anıtkabir', 39.92, 32.85, 3000) is None
    assert o.istekler[0][1].endswith(':searchText') and o.istekler[0][2]['json']['textQuery'] == 'Anıtkabir'


def test_google_anahtarsiz_ve_fabrika(monkeypatch):
    monkeypatch.delenv('GOOGLE_MAPS_API_KEY', raising=False)
    with pytest.raises(HaritaHatasi, match='GOOGLE_MAPS_API_KEY'):
        saglayici_olustur('google')
    assert saglayici_olustur('osm').ad == 'osm'
    with pytest.raises(ValueError):
        saglayici_olustur('yandex')
