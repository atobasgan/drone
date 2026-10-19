import math

import pytest

from mission_executor.planlayici import Hedef, KomutHatasi, Poz, hedef_hesapla

HAVADA = Poz(0.0, 0.0, -10.0, 0.0)


def h(komut, baz=HAVADA, **kw):
    return hedef_hesapla(komut, baz, **kw)


def test_kalk_varsayilan_ve_verilen_irtifa():
    yer = Poz(1, 2, 0, 0)
    assert h({'komut': 'kalk'}, yer, varsayilan_irtifa=10).poz == Poz(1, 2, -10, 0)
    assert h({'komut': 'kalk', 'metre': 25.0}, yer).poz.z == -25


def test_yuksel_goreli_irtifaya_cik_mutlak():
    assert h({'komut': 'yuksel', 'metre': 50}).poz.z == -60
    assert h({'komut': 'alcal', 'metre': 4}).poz.z == -6
    assert h({'komut': 'irtifaya_cik', 'metre': 50}).poz.z == -50


def test_don_sag_saat_yonunde():
    hedef = h({'komut': 'don', 'yon': 'sag', 'derece': 90})
    assert abs(hedef.poz.yaw - math.pi / 2) < 1e-9
    hedef = h({'komut': 'don', 'yon': 'sol', 'derece': 90})
    assert abs(hedef.poz.yaw + math.pi / 2) < 1e-9


def test_don_sonrasi_ileri_baktigi_yone():
    dondu = h({'komut': 'don', 'yon': 'sag', 'derece': 90}).poz
    ileri = h({'komut': 'git_yon', 'yon': 'ileri', 'metre': 20}, dondu).poz
    assert abs(ileri.x) < 1e-9 and abs(ileri.y - 20) < 1e-9 and ileri.z == -10


def test_git_yon_kuzey():
    p = h({'komut': 'git_yon', 'yon': 'kuzey', 'metre': 30}, Poz(0, 0, -10, 2.0)).poz
    assert abs(p.x - 30) < 1e-9 and abs(p.y) < 1e-9


def test_git_koordinat():
    p = h({'komut': 'git_koordinat', 'enlem': 39.9308, 'boylam': 32.8541},
          ref_latlon=(39.9208, 32.8541)).poz
    assert 1100 < p.x < 1125 and p.z == -10
    p = h({'komut': 'git_koordinat', 'enlem': 39.9308, 'boylam': 32.8541, 'metre': 40},
          ref_latlon=(39.9208, 32.8541)).poz
    assert p.z == -40


def test_git_koordinat_referanssiz_hata():
    with pytest.raises(KomutHatasi):
        h({'komut': 'git_koordinat', 'enlem': 39.9, 'boylam': 32.8})


@pytest.mark.parametrize('ad,tip', [
    ('in', 'in'), ('eve_don', 'eve_don'), ('dur', 'dur'),
])
def test_ozel_tipler(ad, tip):
    assert h({'komut': ad}).tip == tip


def test_bekle_ve_hiz():
    assert h({'komut': 'bekle', 'saniye': 3}) == Hedef('bekle', HAVADA, saniye=3.0)
    assert h({'komut': 'hiz_ayarla', 'mps': 5}).mps == 5.0


def test_bilinmeyen_ve_harita():
    with pytest.raises(KomutHatasi):
        h({'komut': 'zipla'})
    with pytest.raises(KomutHatasi):
        h({'komut': 'yakin_yere_git', 'tur': 'hastane'})
