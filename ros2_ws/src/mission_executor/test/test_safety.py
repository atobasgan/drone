"""Her kural icin bir gecen bir kalan ornek (Gorev 1.5)."""
import pytest

from mission_executor.planlayici import Poz
from mission_executor.safety import AracDurumu, Guvenlik, Limitler, Reddedildi

LIM = Limitler(max_irtifa=600, min_irtifa=2, max_adim_mesafe=1000,
               geofence_yaricap=1500, min_batarya=0.25)
G = Guvenlik(LIM)
HAVADA = AracDurumu(poz=Poz(0, 0, -10, 0), havada=True)
YERDE = AracDurumu(poz=Poz(0, 0, 0, 0), havada=False)


def gecer(komut, durum=HAVADA):
    return G.kontrol_et(komut, durum)


def kalir(komut, durum=HAVADA, icerik=None):
    with pytest.raises(Reddedildi) as e:
        G.kontrol_et(komut, durum)
    if icerik:
        assert icerik in str(e.value)


def test_bilinmeyen_komut():
    gecer({'komut': 'yuksel', 'metre': 5})
    kalir({'komut': 'takla_at'}, icerik='bilinmeyen')


def test_eksik_negatif_parametre():
    gecer({'komut': 'git_yon', 'yon': 'ileri', 'metre': 5})
    kalir({'komut': 'git_yon', 'yon': 'ileri', 'metre': 0})
    kalir({'komut': 'yuksel', 'metre': -5})
    kalir({'komut': 'yuksel'})
    kalir({'komut': 'git_yon', 'yon': 'yukari', 'metre': 5})
    kalir({'komut': 'don', 'yon': 'sag', 'derece': 0})
    kalir({'komut': 'don', 'yon': 'ileri', 'derece': 90})
    kalir({'komut': 'bekle', 'saniye': 0})
    kalir({'komut': 'hiz_ayarla', 'mps': 100})
    kalir({'komut': 'git_koordinat', 'enlem': 0, 'boylam': 0})


def test_max_irtifa():
    gecer({'komut': 'yuksel', 'metre': 500})
    kalir({'komut': 'yuksel', 'metre': 5000}, icerik='sınır 600')
    kalir({'komut': 'irtifaya_cik', 'metre': 601})


def test_min_irtifa():
    gecer({'komut': 'alcal', 'metre': 7})
    kalir({'komut': 'alcal', 'metre': 9.5}, icerik='alçak')


def test_max_adim_mesafe():
    gecer({'komut': 'git_yon', 'yon': 'kuzey', 'metre': 1000})
    kalir({'komut': 'git_yon', 'yon': 'kuzey', 'metre': 1200}, icerik='tek adımda')


def test_geofence():
    uzakta = AracDurumu(poz=Poz(1000, 0, -10, 0), havada=True)
    gecer({'komut': 'git_yon', 'yon': 'kuzey', 'metre': 400}, uzakta)
    kalir({'komut': 'git_yon', 'yon': 'kuzey', 'metre': 600}, uzakta, icerik='geofence')


def test_yerdeyken_hareket():
    gecer({'komut': 'kalk'}, YERDE)
    kalir({'komut': 'git_yon', 'yon': 'ileri', 'metre': 5}, YERDE, icerik='kalkış')
    kalir({'komut': 'in'}, YERDE)
    kalir({'komut': 'kalk'}, HAVADA)
    gecer({'komut': 'dur'}, YERDE)


def test_batarya():
    dusuk = AracDurumu(poz=Poz(0, 0, -10, 0), havada=True, batarya=0.1)
    gecer({'komut': 'eve_don'}, dusuk)
    gecer({'komut': 'in'}, dusuk)
    kalir({'komut': 'git_yon', 'yon': 'ileri', 'metre': 5}, dusuk, icerik='batarya')


def test_liste_benzetimi():
    G.liste_kontrol_et([{'komut': 'kalk', 'metre': 10}, {'komut': 'yuksel', 'metre': 20},
                        {'komut': 'git_yon', 'yon': 'kuzey', 'metre': 50}], YERDE)
    # ikinci adim birinciyle birlikte siniri asiyor
    with pytest.raises(Reddedildi, match='adım 2'):
        G.liste_kontrol_et([{'komut': 'yuksel', 'metre': 300},
                            {'komut': 'yuksel', 'metre': 300}], HAVADA)
    # inisten sonra hareket
    with pytest.raises(Reddedildi, match='adım 2'):
        G.liste_kontrol_et([{'komut': 'in'}, {'komut': 'git_yon', 'yon': 'ileri', 'metre': 5}],
                           HAVADA)
