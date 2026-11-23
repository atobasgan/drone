"""Harita komutu -> yurutucu adimlari (ag yok: sahte saglayici)."""
import pytest

from map_tools.yer import HaritaHatasi, Yer
from map_tools.yer_cozucu import Konum, YerCozucu, harita_adimi_var_mi, mesafe_yaz

KIZILAY = Konum(39.9208, 32.8541, irtifa_m=50.0)


class SahteSaglayici:
    def __init__(self, yer=None, hata=None):
        self.yer, self.hata, self.istekler = yer, hata, []

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        self.istekler.append(('en_yakin', tur, enlem, boylam, yaricap_m))
        if self.hata:
            raise HaritaHatasi(self.hata)
        return self.yer

    def ara(self, ad, enlem, boylam, yaricap_m):
        self.istekler.append(('ara', ad, enlem, boylam, yaricap_m))
        return self.yer


HASTANE = Yer('Gazi Hastanesi', 39.9300, 32.8600, 850.0, 'osm')


def test_yakin_yere_git_koordinata_cevrilir():
    s = SahteSaglayici(HASTANE)
    c = YerCozucu(s, seyir_irtifasi_m=30).coz([{'komut': 'yakin_yere_git', 'tur': 'hastane'}], KIZILAY)
    assert c.basarili
    assert c.adimlar == [{'komut': 'git_koordinat', 'enlem': 39.93, 'boylam': 32.86}]   # 50 m > seyir
    assert '850 m uzaktaki Gazi Hastanesi' in c.mesajlar[0]
    assert s.istekler[0][:2] == ('en_yakin', 'hastane')


def test_alcaktaysa_once_seyir_irtifasina_cikar():
    c = YerCozucu(SahteSaglayici(HASTANE), seyir_irtifasi_m=30).coz(
        [{'komut': 'yakin_yere_git', 'tur': 'hastane'}], Konum(39.92, 32.85, irtifa_m=10.0))
    assert [a['komut'] for a in c.adimlar] == ['irtifaya_cik', 'git_koordinat']
    assert c.adimlar[0]['metre'] == 30.0


def test_irtifa_bilinmiyorsa_tirmanir_ve_onceki_adimlari_hesaba_katar():
    cozucu = YerCozucu(SahteSaglayici(HASTANE), seyir_irtifasi_m=30)
    c = cozucu.coz([{'komut': 'yakin_yere_git', 'tur': 'hastane'}], Konum(39.92, 32.85))
    assert c.adimlar[0] == {'komut': 'irtifaya_cik', 'metre': 30.0}
    # "40 m'ye çık sonra en yakın hastaneye git": zaten yuksekte, ek tirmanma yok
    c = cozucu.coz([{'komut': 'irtifaya_cik', 'metre': 40.0}, {'komut': 'yakin_yere_git', 'tur': 'hastane'}],
                   Konum(39.92, 32.85, irtifa_m=5.0))
    assert [a['komut'] for a in c.adimlar] == ['irtifaya_cik', 'git_koordinat']


def test_uzak_ya_da_yoksa_hic_adim_uretmez():
    uzak = Yer('Uzak Hastane', 39.95, 32.90, 4200.0, 'osm')
    c = YerCozucu(SahteSaglayici(uzak), en_uzak_m=1000).coz(
        [{'komut': 'kalk'}, {'komut': 'yakin_yere_git', 'tur': 'hastane'}], KIZILAY)
    assert not c.basarili and '4.2 km' in c.hata and 'sınır 1.0 km' in c.hata
    c = YerCozucu(SahteSaglayici(None)).coz([{'komut': 'yakin_yere_git', 'tur': 'eczane'}], KIZILAY)
    assert not c.basarili and 'eczane bulunamadı' in c.hata


def test_servis_hatasi_reddedilir():
    c = YerCozucu(SahteSaglayici(hata='harita servisine ulaşılamadı')).coz(
        [{'komut': 'yakin_yere_git', 'tur': 'park'}], KIZILAY)
    assert not c.basarili and 'ulaşılamadı' in c.hata


def test_yere_git_isimle_arar():
    s = SahteSaglayici(Yer('Anıtkabir', 39.9255, 32.8369, 1700.0, 'osm'))
    c = YerCozucu(s, en_uzak_m=2000).coz([{'komut': 'yere_git', 'ad': 'Anıtkabir'}], KIZILAY)
    assert c.basarili and s.istekler[0][:2] == ('ara', 'Anıtkabir')
    assert c.adimlar[-1]['komut'] == 'git_koordinat'


def test_harita_disi_komutlar_ve_seyir_ayari():
    cozucu = YerCozucu(SahteSaglayici(), seyir_irtifasi_m=30, git_koordinata_seyir=True)
    assert not cozucu.gerekli_mi([{'komut': 'kalk'}, {'komut': 'yuksel', 'metre': 5.0}])
    gk = [{'komut': 'git_koordinat', 'enlem': 39.93, 'boylam': 32.86}]
    assert cozucu.gerekli_mi(gk)                                     # 5.1: LLM'in git_koordinat'i da
    assert cozucu.coz(gk, Konum(39.92, 32.85, 10.0)).adimlar[0]['komut'] == 'irtifaya_cik'
    kapali = YerCozucu(SahteSaglayici(), seyir_irtifasi_m=0)
    assert not kapali.gerekli_mi(gk)


def test_gps_yoksa_uyarir():
    adimlar = [{'komut': 'yakin_yere_git', 'tur': 'hastane'}]
    c = YerCozucu(SahteSaglayici(HASTANE)).coz(adimlar, Konum(39.92, 32.85, 50.0, gps=False))
    assert any('GPS yok' in m for m in c.mesajlar)


def test_yardimcilar():
    assert mesafe_yaz(850) == '850 m' and mesafe_yaz(1234) == '1.2 km'
    assert harita_adimi_var_mi([{'komut': 'yere_git', 'ad': 'x'}])
    with pytest.raises(KeyError):
        YerCozucu(SahteSaglayici(HASTANE)).coz([{'komut': 'yakin_yere_git', 'tur': 'kafe'}], KIZILAY)
