"""Cekirdek mantigi: sahte saat + sahte ROS ile."""
import json
import struct

import pytest

from mobile_bridge import protokol as p
from mobile_bridge.cekirdek import HERKES, Ayarlar, RosArayuzu, TelsizCekirdegi


class SahteRos(RosArayuzu):
    def __init__(self):
        self.metinler, self.acil, self.konusmalar, self.stt = [], 0, [], []

    def metin_yayinla(self, metin):
        self.metinler.append(metin)

    def acil_dur_yayinla(self):
        self.acil += 1

    def konusma_yayinla(self, konusma, kaynak):
        self.konusmalar.append((konusma.konusma_id, kaynak))

    def stt_baslat(self, konusma):
        self.stt.append(konusma)


class Saat:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def tipler(cikti):
    return [json.loads(m)['tip'] for _, m in cikti]


def mesaj(cikti, tip):
    return next(json.loads(m) for _, m in cikti if json.loads(m)['tip'] == tip)


@pytest.fixture
def ortam(tmp_path):
    ros, saat = SahteRos(), Saat()
    c = TelsizCekirdegi(ros, Ayarlar(token='gizli', kayit_klasoru=str(tmp_path)), saat=saat,
                        stt_hazir=True, stt_adi='sahte')
    return c, ros, saat, tmp_path


def giris(c, ad='tel', rol='operator', token='gizli'):
    i = c.baglandi(ad)
    cikti = c.metin_cercevesi(i, p.json_yaz('merhaba', token=token, rol=rol, cihaz=ad))
    return i, cikti


def ses(c, i, kid, sure_s, sira0=0, parca=640):
    pcm = struct.pack('<h', 1000) * int(16000 * sure_s)
    for n, k in enumerate(range(0, len(pcm), parca)):
        c.ikili_cerceve(i, p.ses_parcasi_yaz(kid, sira0 + n, pcm[k:k + parca]))


def test_token_hatali_ise_yetkisiz(ortam):
    c, ros, *_ = ortam
    i, cikti = giris(c, token='yanlis')
    assert mesaj(cikti, 'hata')['kod'] == 'yetkisiz'
    assert tipler(c.metin_cercevesi(i, p.json_yaz('metin', id=1, metin='kalk'))) == ['hata']
    assert ros.metinler == []


def test_giris_ve_tek_operator(ortam):
    c, *_ = ortam
    a, cikti = giris(c, 'a')
    hos = mesaj(cikti, 'hos_geldin')
    assert hos['rol'] == 'operator' and hos['yer_stt'] is True
    b, cikti = giris(c, 'b')
    assert mesaj(cikti, 'hos_geldin')['rol'] == 'izleyici'
    assert mesaj(cikti, 'hata')['kod'] == 'operator_dolu'
    assert mesaj(c.metin_cercevesi(b, p.json_yaz('metin', id=1, metin='kalk')), 'hata')['kod'] \
        == 'operator_degil'


def test_izleyici_de_acil_dur_verebilir(ortam):
    c, ros, *_ = ortam
    giris(c, 'a')
    b, _ = giris(c, 'b', rol='izleyici')
    cikti = c.metin_cercevesi(b, p.json_yaz('acil_dur'))
    assert ros.acil == 1 and cikti[0][0] is HERKES
    assert mesaj(cikti, 'geri_bildirim')['durum'] == 'acil_dur'


def test_metin_modu_ve_komut_eslestirme(ortam):
    c, ros, saat, _ = ortam
    i, _ = giris(c)
    cikti = c.metin_cercevesi(i, p.json_yaz('metin', id=7, metin=' 20 metre yüksel '))
    assert ros.metinler == ['20 metre yüksel']
    assert mesaj(cikti, 'duyuldu') == {'tip': 'duyuldu', 'id': 7, 'metin': '20 metre yüksel',
                                       'kaynak': 'telefon_stt', 'stt_ms': None}
    saat.t += 0.012
    k = mesaj(c.ros_komut({'metin': '20 m yüksel', 'kaynak': 'hizli_yol', 'kuyruga_ekle': False,
                           'adimlar': [{'komut': 'yuksel', 'metre': 20}], 'parser_ms': 0.1}), 'komut')
    assert k['id'] == 7 and k['gecikme_ms'] == 12 and k['adimlar'][0]['komut'] == 'yuksel'
    # yurutucunun geri bildirimi son komuta baglanir
    gb = mesaj(c.ros_geri_bildirim('yurutuyor', '20 metre yükseliyorum'), 'geri_bildirim')
    assert gb['id'] == 7


def test_anlamadim_bekleyen_konusmaya_baglanir(ortam):
    c, ros, *_ = ortam
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('metin', id=3, metin='saat kaç'))
    a = mesaj(c.ros_geri_bildirim('reddedildi', 'anlamadım: "saat kaç"'), 'anlasilmadi')
    assert a['id'] == 3


def test_eslestirme_zaman_asimi(ortam):
    c, ros, saat, _ = ortam
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('metin', id=1, metin='kalk'))
    saat.t += 60
    assert mesaj(c.ros_komut({'adimlar': []}), 'komut')['id'] is None


def test_ses_modu_stt_ve_kayit(ortam):
    c, ros, saat, klasor = ortam
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('ptt_basla', id=5))
    ses(c, i, 5, 1.0)
    cikti = c.metin_cercevesi(i, p.json_yaz('ptt_bitti', id=5))
    isl = mesaj(cikti, 'isleniyor')
    assert isl['sure_ms'] == 1000 and isl['kayip_parca'] == 0
    assert ros.konusmalar == [(5, 'telefon')] and len(ros.stt) == 1
    k = ros.stt[0]
    assert len(k.pcm()) == 32000
    cikti = c.stt_sonucu(k, '20 metre yüksel', 230.4)
    assert mesaj(cikti, 'duyuldu')['stt_ms'] == 230 and ros.metinler == ['20 metre yüksel']
    wavlar = list(klasor.glob('*.wav'))
    assert len(wavlar) == 1
    assert (klasor / 'etiketler.csv').read_text(encoding='utf-8').splitlines()[1] == \
        f'{wavlar[0].name};20 metre yüksel;'


def test_parcalar_sirasiz_gelse_de_birlesir(ortam):
    c, ros, *_ = ortam
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('ptt_basla', id=1))
    a, b = struct.pack('<h', 1) * 4000, struct.pack('<h', 2) * 4000
    c.ikili_cerceve(i, p.ses_parcasi_yaz(1, 1, b))
    c.ikili_cerceve(i, p.ses_parcasi_yaz(1, 0, a))
    c.ikili_cerceve(i, p.ses_parcasi_yaz(1, 1, b))          # tekrar
    c.metin_cercevesi(i, p.json_yaz('ptt_bitti', id=1))
    assert ros.stt[0].pcm() == a + b


def test_kisa_uzun_iptal_ve_eski_parca(ortam):
    c, ros, *_ = ortam
    c.ayarlar.en_uzun_konusma_s = 1.0
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('ptt_basla', id=1))
    ses(c, i, 1, 0.1)
    cikti = c.metin_cercevesi(i, p.json_yaz('ptt_bitti', id=1))
    assert 'çok kısa' in mesaj(cikti, 'anlasilmadi')['sebep']
    c.metin_cercevesi(i, p.json_yaz('ptt_basla', id=2))
    pcm = b'\x00\x00' * 17000
    hata = c.ikili_cerceve(i, p.ses_parcasi_yaz(2, 0, pcm))
    assert mesaj(hata, 'hata')['kod'] == 'konusma_cok_uzun'
    c.metin_cercevesi(i, p.json_yaz('ptt_basla', id=3))
    c.metin_cercevesi(i, p.json_yaz('ptt_iptal', id=3))
    assert c.ikili_cerceve(i, p.ses_parcasi_yaz(3, 0, b'\x00\x00')) == []
    assert mesaj(c.metin_cercevesi(i, p.json_yaz('ptt_bitti', id=3)), 'hata')['kod'] == 'konusma_yok'
    assert ros.stt == []


def test_yer_stt_yoksa_bilgilendirir(tmp_path):
    ros = SahteRos()
    c = TelsizCekirdegi(ros, Ayarlar(token='gizli'), saat=Saat(), stt_hazir=False)
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('ptt_basla', id=1))
    ses(c, i, 1, 0.5)
    sebep = mesaj(c.metin_cercevesi(i, p.json_yaz('ptt_bitti', id=1)), 'anlasilmadi')['sebep']
    assert 'telefonda tanı' in sebep and ros.stt == []
    assert ros.konusmalar == [(1, 'telefon')]     # Faz 3 stt_node yine de alabilir


def test_kalp_atisi_kesilince_dur(ortam):
    c, ros, saat, _ = ortam
    i, _ = giris(c)
    saat.t += 2
    assert c.tik() == []
    c.metin_cercevesi(i, p.json_yaz('ping', t=1))
    saat.t += 3.5
    cikti = c.tik()
    assert ros.acil == 1 and mesaj(cikti, 'geri_bildirim')['durum'] == 'telsiz_koptu'
    saat.t += 5
    assert c.tik() == [] and ros.acil == 1          # bir kez


def test_yerdeyken_kopma_dur_gondermez(ortam):
    c, ros, saat, _ = ortam
    i, _ = giris(c)
    c.telemetri({'havada': False, 'irtifa': 0})
    c.koptu(i)
    assert ros.acil == 0


def test_devam_ayari_ve_yeniden_baglanma(ortam):
    c, ros, saat, _ = ortam
    c.ayarlar.baglanti_koparsa = 'devam'
    i, _ = giris(c)
    cikti = c.koptu(i)
    assert ros.acil == 0 and 'devam' in mesaj(cikti, 'geri_bildirim')['mesaj']
    j, cikti = giris(c, 'yeni')
    assert mesaj(cikti, 'hos_geldin')['rol'] == 'operator'


def test_hos_geldinde_son_telemetri(ortam):
    c, *_ = ortam
    c.telemetri({'irtifa': 12.3, 'havada': True})
    _, cikti = giris(c)
    assert mesaj(cikti, 'telemetri')['irtifa'] == 12.3


def test_acil_dur_ile_iptal_edilen_sonuc_bekleyene_baglanir(ortam):
    c, ros, *_ = ortam
    i, _ = giris(c)
    c.metin_cercevesi(i, p.json_yaz('metin', id=9, metin='önce on metre yüksel sonra doğuya git'))
    gb = mesaj(c.ros_geri_bildirim('iptal', 'ACİL DUR geldiği için "..." iptal edildi'), 'geri_bildirim')
    assert gb['id'] == 9 and gb['durum'] == 'reddedildi'
