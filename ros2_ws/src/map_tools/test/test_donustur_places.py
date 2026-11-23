"""donustur (mesaj <-> sozluk) ve places_node.sorgula (servis cekirdegi) testleri."""
import os
import sys

from map_tools.donustur import KOPYALANAN_ALANLAR, dur_mu, msg_to_adim, yeni_liste
from map_tools.yer import HaritaHatasi, Yer

try:                                    # ROS kurulu degilse sahte rclpy/drone_interfaces
    import rclpy  # noqa: F401
    from drone_interfaces.srv import FindNearest  # noqa: F401
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'araclar', 'sahte_sim',
                                    'stubs'))
from map_tools.places_node import sorgula  # noqa: E402


class SahteKomut:
    def __init__(self, **kw):
        self.komut, self.metre, self.derece, self.yon = '', 0.0, 0.0, ''
        self.enlem = self.boylam = self.saniye = self.mps = 0.0
        self.tur = self.ad = ''
        self.__dict__.update(kw)


class SahteListe:
    def __init__(self, **kw):
        self.adimlar = []
        for alan in KOPYALANAN_ALANLAR:
            setattr(self, alan, None)
        self.__dict__.update(kw)


def test_msg_to_adim_yere_git_ve_digerleri():
    assert msg_to_adim(SahteKomut(komut='yere_git', ad='Anıtkabir')) == {'komut': 'yere_git', 'ad': 'Anıtkabir'}
    assert msg_to_adim(SahteKomut(komut='yakin_yere_git', tur='hastane')) == {'komut': 'yakin_yere_git',
                                                                              'tur': 'hastane'}
    assert msg_to_adim(SahteKomut(komut='kalk', metre=10.0)) == {'komut': 'kalk', 'irtifa_m': 10.0}


def test_yeni_liste_zaman_damgalarini_ve_kaynagi_tasir():
    eski = SahteListe(t_komut_hazir='t2', metin='en yakın hastaneye git', kaynak='hizli_yol', kuyruga_ekle=True)
    yeni = yeni_liste(eski, [{'komut': 'irtifaya_cik', 'metre': 30.0},
                             {'komut': 'git_koordinat', 'enlem': 39.93, 'boylam': 32.86}], SahteListe, SahteKomut)
    assert (yeni.t_komut_hazir, yeni.metin, yeni.kaynak, yeni.kuyruga_ekle) == ('t2', eski.metin, 'hizli_yol', True)
    assert [a.komut for a in yeni.adimlar] == ['irtifaya_cik', 'git_koordinat']
    assert yeni.adimlar[1].enlem == 39.93 and yeni.adimlar[0].metre == 30.0


def test_dur_mu():
    assert dur_mu(SahteListe(adimlar=[SahteKomut(komut='dur')]))
    assert not dur_mu(SahteListe(adimlar=[SahteKomut(komut='kalk', metre=5.0)]))
    assert not dur_mu(SahteListe())


class Saglayici:
    def __init__(self, yer=None, hata=None):
        self.yer, self.hata = yer, hata

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        if self.hata:
            raise HaritaHatasi(self.hata)
        return self.yer

    def ara(self, ad, enlem, boylam, yaricap_m):
        return self.yer


def test_sorgula():
    yer = Yer('Gazi Hastanesi', 39.93, 32.86, 850.0, 'osm')
    assert sorgula(Saglayici(yer), 'hastane', '', 39.92, 32.85, 3000) == (yer, '')
    assert sorgula(Saglayici(yer), '', 'Gazi', 39.92, 32.85, 3000) == (yer, '')
    assert sorgula(Saglayici(), 'hastane', '', 39.92, 32.85, 3000) == (None, '3000 m içinde bulunamadı')
    assert sorgula(Saglayici(hata='zaman aşımı'), 'hastane', '', 0, 0, 1) == (None, 'zaman aşımı')
    assert sorgula(Saglayici(yer), '', '', 0, 0, 1) == (None, 'tur ya da ad verilmeli')
