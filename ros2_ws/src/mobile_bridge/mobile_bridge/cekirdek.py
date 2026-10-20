"""Telsiz koprusunun cekirdegi: oturum, yetki, konusma biriktirme, eslestirme.

ROS'tan ve agdan bagimsizdir. Her olay (mesaj geldi, ses geldi, baglanti koptu,
STT bitti, ROS'tan geri bildirim geldi...) bir metotla cekirdege verilir;
cekirdek telefonlara gidecek mesajlari [(alici, metin), ...] olarak dondurur ve
ROS tarafindaki isleri RosArayuzu uzerinden yapar. Boylece tum mantik sahte
saat ve sahte ROS ile birim test edilebilir (test/test_cekirdek.py).
"""
from collections import deque
from dataclasses import dataclass, field
import hmac
import os
import time

from . import protokol as p
from .ses import Konusma, sure_s, wav_kaydet

HERKES = object()          # alici: tum dogrulanmis istemciler


@dataclass
class Ayarlar:
    token: str = ''
    tek_operator: bool = True
    en_uzun_konusma_s: float = 15.0
    en_kisa_konusma_s: float = 0.25
    baglanti_zaman_asimi_s: float = 3.0
    baglanti_koparsa: str = 'dur'          # dur | devam
    eslestirme_zaman_asimi_s: float = 15.0
    kayit_klasoru: str = ''                # bos = kayit yok


class RosArayuzu:
    """Cekirdegin ROS'tan istedikleri. bridge_node gercegini, testler sahtesini verir."""

    def metin_yayinla(self, metin):
        raise NotImplementedError

    def acil_dur_yayinla(self):
        raise NotImplementedError

    def konusma_yayinla(self, konusma, kaynak):
        """drone_interfaces/AudioUtterance (varsa). Zorunlu degil."""

    def stt_baslat(self, konusma):
        """Sesi arka planda yaziya cevirir; bitince cekirdek.stt_sonucu cagrilir."""
        raise NotImplementedError


@dataclass(eq=False)          # kimlige gore karsilastir; sozluk anahtari olabilsin
class Istemci:
    ad: str
    dogrulandi: bool = False
    rol: str = 'izleyici'
    cihaz: str = ''
    son_mesaj_t: float = 0.0
    konusma: Konusma = None


@dataclass
class _Bekleyen:
    konusma_id: int
    t: float
    istemci: Istemci = field(repr=False, default=None)


class TelsizCekirdegi:

    def __init__(self, ros, ayarlar=None, saat=time.monotonic, stt_hazir=False, stt_adi='yok'):
        self.ros = ros
        self.ayarlar = ayarlar or Ayarlar()
        self.saat = saat
        self.stt_hazir = stt_hazir
        self.stt_adi = stt_adi
        self.istemciler = []
        self.operator = None
        self._bekleyen = deque()        # metni yayinlanan, komutu beklenen konusmalar
        self._son_komut_id = None
        self._son_komut_t = 0.0
        self._kopma_bildirildi = False
        self.havada = None              # telemetriden; None = bilinmiyor
        self.son_telemetri = None
        self.sayaclar = {'konusma': 0, 'metin': 0, 'acil_dur': 0, 'red': 0, 'kayip_parca': 0}

    # ------------------------------------------------------------------ baglanti
    def baglandi(self, ad):
        istemci = Istemci(ad=ad, son_mesaj_t=self.saat())
        self.istemciler.append(istemci)
        return istemci

    def koptu(self, istemci):
        cikti = []
        if istemci in self.istemciler:
            self.istemciler.remove(istemci)
        if istemci is self.operator:
            self.operator = None
            cikti += self._operator_kayboldu('operatör bağlantısı kapandı')
        return cikti

    # ------------------------------------------------------------------ gelenler
    def metin_cercevesi(self, istemci, ham):
        try:
            mesaj = p.json_coz(ham)
        except p.ProtokolHatasi as e:
            return [(istemci, p.json_yaz('hata', kod=e.kod, mesaj=str(e)))]
        istemci.son_mesaj_t = self.saat()
        tip = mesaj['tip']

        if tip == 'merhaba':
            return self._merhaba(istemci, mesaj)
        if not istemci.dogrulandi:
            return [(istemci, p.json_yaz('hata', kod='yetkisiz', mesaj='önce merhaba ile giriş yap'))]
        if tip == 'ping':
            return [(istemci, p.json_yaz('pong', t=mesaj.get('t'), sunucu_saati=time.time()))]
        if tip == 'acil_dur':
            # Guvenlik: izleyici dahil her dogrulanmis istemci durdurabilir.
            self.sayaclar['acil_dur'] += 1
            self.ros.acil_dur_yayinla()
            return [(HERKES, p.json_yaz('geri_bildirim', id=None, durum='acil_dur',
                                        mesaj=f'ACİL DUR ({istemci.cihaz or istemci.ad})'))]

        if istemci is not self.operator:
            return [(istemci, p.json_yaz('hata', kod='operator_degil',
                                         mesaj='komut vermek için operatör olmalısın'))]
        if tip == 'ptt_basla':
            return self._ptt_basla(istemci, mesaj)
        if tip == 'ptt_iptal':
            if istemci.konusma and istemci.konusma.konusma_id == mesaj['id']:
                istemci.konusma = None
            return []
        if tip == 'ptt_bitti':
            return self._ptt_bitti(istemci, mesaj)
        if tip == 'metin':
            return self._metin(istemci, mesaj)
        return []

    def ikili_cerceve(self, istemci, veri):
        if not istemci.dogrulandi or istemci is not self.operator:
            return []
        try:
            konusma_id, sira, pcm = p.ses_parcasi_coz(veri)
        except p.ProtokolHatasi as e:
            return [(istemci, p.json_yaz('hata', kod=e.kod, mesaj=str(e)))]
        istemci.son_mesaj_t = self.saat()
        k = istemci.konusma
        if k is None or k.konusma_id != konusma_id:
            return []                   # iptal edilmis ya da eski konusma
        en_fazla = int(self.ayarlar.en_uzun_konusma_s * p.ORNEKLEME_HZ * p.ORNEK_BAYT)
        if not k.ekle(sira, pcm, en_fazla):
            istemci.konusma = None
            sinir = self.ayarlar.en_uzun_konusma_s
            return [(istemci, p.json_yaz('hata', kod='konusma_cok_uzun', id=konusma_id,
                                         mesaj=f'konuşma {sinir:g} sn sınırını aştı'))]
        return []

    # ------------------------------------------------------------------ mesaj tipleri
    def _merhaba(self, istemci, mesaj):
        if not self.ayarlar.token or not hmac.compare_digest(
                mesaj['token'].encode(), self.ayarlar.token.encode()):
            return [(istemci, p.json_yaz('hata', kod='yetkisiz', mesaj='token hatalı'))]
        if mesaj.get('surum', p.SURUM) != p.SURUM:
            return [(istemci, p.json_yaz('hata', kod='surum',
                                         mesaj=f'protokol sürümü {p.SURUM} bekleniyor'))]
        istemci.dogrulandi = True
        istemci.cihaz = str(mesaj.get('cihaz', ''))[:60]
        cikti = []
        istenen = mesaj['rol']
        if istenen == 'operator' and (self.operator is None or not self.ayarlar.tek_operator):
            istemci.rol = 'operator'
            self.operator = istemci
            self._kopma_bildirildi = False
        else:
            istemci.rol = 'izleyici'
            if istenen == 'operator':
                cikti.append((istemci, p.json_yaz(
                    'hata', kod='operator_dolu',
                    mesaj='başka bir operatör bağlı; izleyici olarak bağlandın')))
        cikti.insert(0, (istemci, p.json_yaz(
            'hos_geldin', surum=p.SURUM, rol=istemci.rol,
            yer_stt=self.stt_hazir, stt_motoru=self.stt_adi,
            ses={'bicim': 'pcm16', 'hz': p.ORNEKLEME_HZ, 'kanal': 1},
            en_uzun_konusma_s=self.ayarlar.en_uzun_konusma_s,
            sunucu_saati=time.time())))
        if self.son_telemetri:
            cikti.append((istemci, p.json_yaz('telemetri', **self.son_telemetri)))
        return cikti

    def _ptt_basla(self, istemci, mesaj):
        istemci.konusma = Konusma(konusma_id=mesaj['id'], t_basla=self.saat())
        return []

    def _ptt_bitti(self, istemci, mesaj):
        k = istemci.konusma
        if k is None or k.konusma_id != mesaj['id']:
            return [(istemci, p.json_yaz('hata', kod='konusma_yok', id=mesaj['id'],
                                         mesaj='bu id ile başlatılmış konuşma yok'))]
        istemci.konusma = None
        k.t_bitti = self.saat()
        pcm = k.pcm()
        sure = sure_s(pcm)
        eksik = k.eksik_parcalar()
        if eksik:
            self.sayaclar['kayip_parca'] += len(eksik)
        if sure < self.ayarlar.en_kisa_konusma_s:
            return [(istemci, p.json_yaz('anlasilmadi', id=k.konusma_id,
                                         sebep=f'konuşma çok kısa ({sure * 1000:.0f} ms)'))]
        self.sayaclar['konusma'] += 1
        self.ros.konusma_yayinla(k, 'telefon')
        self._kaydet(k, pcm)
        if not self.stt_hazir:
            return [(istemci, p.json_yaz(
                'anlasilmadi', id=k.konusma_id,
                sebep='yer istasyonunda STT yok; ayarlardan "telefonda tanı" moduna geç'))]
        self.ros.stt_baslat(k)
        return [(istemci, p.json_yaz('isleniyor', id=k.konusma_id, sure_ms=round(sure * 1000),
                                     kayip_parca=len(eksik)))]

    def _metin(self, istemci, mesaj):
        metin = mesaj['metin'].strip()
        if not metin:
            return [(istemci, p.json_yaz('anlasilmadi', id=mesaj['id'], sebep='boş metin'))]
        self.sayaclar['metin'] += 1
        return self._metni_gonder(istemci, mesaj['id'], metin[:500],
                                  kaynak=str(mesaj.get('kaynak', 'telefon_stt')), stt_ms=None)

    def _metni_gonder(self, istemci, konusma_id, metin, kaynak, stt_ms):
        self._bekleyen.append(_Bekleyen(konusma_id, self.saat(), istemci))
        self.ros.metin_yayinla(metin)
        return [(HERKES, p.json_yaz('duyuldu', id=konusma_id, metin=metin, kaynak=kaynak,
                                    stt_ms=stt_ms))]

    def _kaydet(self, k, pcm):
        klasor = self.ayarlar.kayit_klasoru
        if not klasor:
            return
        ad = time.strftime('%Y%m%d_%H%M%S') + f'_{k.konusma_id:05d}.wav'
        k.kayit_yolu = os.path.join(klasor, ad)
        wav_kaydet(k.kayit_yolu, pcm)

    # ------------------------------------------------------------------ STT sonucu
    def stt_sonucu(self, konusma, metin, sure_ms, hata=None):
        istemci = self.operator
        self._etiket_yaz(konusma, metin or '')
        if hata or not metin:
            return [(HERKES, p.json_yaz('anlasilmadi', id=konusma.konusma_id,
                                        sebep=hata or 'ses yazıya çevrilemedi (boş)', stt_ms=sure_ms))]
        return self._metni_gonder(istemci, konusma.konusma_id, metin, kaynak='yer_stt',
                                  stt_ms=round(sure_ms))

    def _etiket_yaz(self, konusma, metin):
        """Kayit acikken: dosya;stt_metni;beklenen (beklenen elle doldurulur, Gorev 3.1)."""
        yol = konusma.kayit_yolu
        if not yol:
            return
        csv_yol = os.path.join(self.ayarlar.kayit_klasoru, 'etiketler.csv')
        yeni = not os.path.exists(csv_yol)
        with open(csv_yol, 'a', encoding='utf-8') as f:
            if yeni:
                f.write('dosya;stt_metni;beklenen_metin\n')
            f.write(f'{os.path.basename(yol)};{metin.replace(";", ",")};\n')

    # ------------------------------------------------------------------ ROS'tan gelenler
    def _eslestir(self):
        """Parser'in urettigi sonucu en eski bekleyen konusmayla eslestirir."""
        simdi = self.saat()
        while self._bekleyen and simdi - self._bekleyen[0].t > self.ayarlar.eslestirme_zaman_asimi_s:
            self._bekleyen.popleft()
        return self._bekleyen.popleft() if self._bekleyen else None

    def ros_komut(self, komut):
        """/drone/command geldi. komut: {'metin','kaynak','kuyruga_ekle','adimlar','parser_ms'}"""
        bekleyen = self._eslestir()
        konusma_id = bekleyen.konusma_id if bekleyen else None
        gecikme = round((self.saat() - bekleyen.t) * 1000) if bekleyen else None
        self._son_komut_id, self._son_komut_t = konusma_id, self.saat()
        return [(HERKES, p.json_yaz('komut', id=konusma_id, gecikme_ms=gecikme, **komut))]

    def ros_geri_bildirim(self, durum, mesaj):
        """/drone/feedback geldi. Parser'in 'anlamadim' cevabi bekleyen konusmaya baglanir."""
        if durum == 'iptal':
            # Parser bu konusmanin sonucunu ACIL DUR yuzunden atti.
            bekleyen = self._eslestir()
            return [(HERKES, p.json_yaz('geri_bildirim', id=bekleyen.konusma_id if bekleyen else None,
                                        durum='reddedildi', mesaj=mesaj))]
        if durum == 'reddedildi' and mesaj.startswith('anlamadım'):
            bekleyen = self._eslestir()
            self.sayaclar['red'] += 1
            return [(HERKES, p.json_yaz('anlasilmadi', id=bekleyen.konusma_id if bekleyen else None,
                                        sebep=mesaj))]
        konusma_id = None
        if self._son_komut_id is not None and self.saat() - self._son_komut_t < 120:
            konusma_id = self._son_komut_id
        return [(HERKES, p.json_yaz('geri_bildirim', id=konusma_id, durum=durum, mesaj=mesaj))]

    def telemetri(self, veri):
        self.son_telemetri = veri
        self.havada = veri.get('havada')
        return [(HERKES, p.json_yaz('telemetri', **veri))]

    # ------------------------------------------------------------------ zamanlayici
    def tik(self):
        """Duzenli cagrilir (ornegin 0.5 sn'de bir): operator kalp atisi kontrolu."""
        op = self.operator
        if op is None or self._kopma_bildirildi:
            return []
        if self.saat() - op.son_mesaj_t > self.ayarlar.baglanti_zaman_asimi_s:
            return self._operator_kayboldu(
                f'operatörden {self.ayarlar.baglanti_zaman_asimi_s:g} sn sinyal yok')
        return []

    def _operator_kayboldu(self, sebep):
        if self._kopma_bildirildi:
            return []
        self._kopma_bildirildi = True
        eylem = 'devam ediyor'
        if self.ayarlar.baglanti_koparsa == 'dur' and self.havada is not False:
            self.ros.acil_dur_yayinla()
            eylem = 'drone yerinde asılı kalıyor'
        return [(HERKES, p.json_yaz('geri_bildirim', id=None, durum='telsiz_koptu',
                                    mesaj=f'{sebep}; {eylem}'))]

    def durum_ozeti(self):
        return {
            'istemci': len(self.istemciler),
            'operator': self.operator.cihaz if self.operator else None,
            **self.sayaclar,
        }
