"""OnbellekliSaglayici: ayni sorgu tekrar servise gitmez, hata onbellege girmez, sure dolunca yenilenir."""
import pytest

from map_tools.fabrika import saglayici_olustur
from map_tools.onbellek import OnbellekliSaglayici
from map_tools.yer import HaritaHatasi, Yer


class Sayac:
    ad = 'sayac'

    def __init__(self, yer=None):
        self.yer, self.cagri, self.hata = yer, 0, None

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        self.cagri += 1
        if self.hata:
            raise HaritaHatasi(self.hata)
        return self.yer

    ara = en_yakin


HASTANE = Yer('Gazi Hastanesi', 39.9300, 32.8600, 0.0, 'osm')


def test_ayni_sorgu_bir_kez_gider_mesafe_guncellenir():
    zaman = [0.0]
    ic = Sayac(HASTANE)
    s = OnbellekliSaglayici(ic, sure_s=600, saat=lambda: zaman[0])
    y1 = s.en_yakin('hastane', 39.9208, 32.8541, 3000)
    y2 = s.en_yakin('hastane', 39.92082, 32.85412, 3000)        # ~3 m ote: ayni hucre
    assert ic.cagri == 1 and y1.ad == y2.ad == 'Gazi Hastanesi'
    assert y1.mesafe_m > 1000 and y1.mesafe_m != y2.mesafe_m
    s.en_yakin('eczane', 39.9208, 32.8541, 3000)                  # baska tur
    s.en_yakin('hastane', 39.9300, 32.8541, 3000)                 # 1 km kuzey: baska hucre
    assert ic.cagri == 3
    zaman[0] = 601.0
    s.en_yakin('hastane', 39.9208, 32.8541, 3000)                 # sure doldu
    assert ic.cagri == 4


def test_bulunamadi_onbellege_girer_hata_girmez():
    ic = Sayac(None)
    s = OnbellekliSaglayici(ic)
    assert s.ara('Yok Yeri', 39.92, 32.85, 3000) is None
    assert s.ara('yok yeri', 39.92, 32.85, 3000) is None and ic.cagri == 1
    ic.hata = 'zaman aşımı'
    with pytest.raises(HaritaHatasi):
        s.en_yakin('park', 39.92, 32.85, 3000)
    with pytest.raises(HaritaHatasi):
        s.en_yakin('park', 39.92, 32.85, 3000)
    assert ic.cagri == 3


def test_fabrika():
    assert isinstance(saglayici_olustur('osm'), OnbellekliSaglayici)
    assert saglayici_olustur('osm', onbellek_s=0).ad == 'osm'
    with pytest.raises(ValueError):
        saglayici_olustur('bing')
