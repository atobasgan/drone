"""Harita komutlarini yurutucunun bildigi adimlara cevirir (ROS'tan bagimsiz, Gorev 5.1 - 5.4).

    yakin_yere_git {tur}  ┐                       ┌ irtifaya_cik {seyir}   (alcaktaysa, 5.1)
    yere_git {ad}         ┴─> harita servisi ─>   └ git_koordinat {enlem, boylam}

Yurutucu (mission_executor) hic degismez: o yalnizca git_koordinat'i gorur.
Kurallar:
  - Yer bulunamazsa ya da en_uzak_m'den uzaksa HIC adim uretilmez, sebep bildirilir.
    (Bir adimi yapip digerini yapmamak, yarim kalmis bir gorev demektir.)
  - Gorev 5.1 "once guvenli seyir irtifasina cik, sonra yatay git": drone seyir irtifasinin
    altindaysa (ya da irtifa bilinmiyorsa) git_koordinat'in onune irtifaya_cik eklenir.
  - Ortuk kalkis YOK: drone yerdeyse yurutucu "once kalkis yapmalıyım" diye reddeder.
"""
from dataclasses import dataclass, field

from .turler import tur_bilgisi
from .yer import HaritaHatasi

HARITA_KOMUTLARI = ('yakin_yere_git', 'yere_git')


@dataclass
class Konum:
    enlem: float
    boylam: float
    irtifa_m: float = None      # yerden; None = bilinmiyor
    gps: bool = True            # False: GPS yok, varsayilan (kalkis) konum kullanildi


@dataclass
class Cozum:
    adimlar: list = None        # None = reddedildi
    mesajlar: list = field(default_factory=list)
    hata: str = ''

    @property
    def basarili(self):
        return self.adimlar is not None


def mesafe_yaz(metre):
    return f'{metre / 1000:.1f} km' if metre >= 1000 else f'{metre:.0f} m'


def harita_adimi_var_mi(adimlar):
    return any(a['komut'] in HARITA_KOMUTLARI for a in adimlar)


def irtifa_sonrasi(adim, irtifa):
    """Bir adimdan sonra drone'un irtifasi (biliniyorsa). Seyir karari icin."""
    k = adim['komut']
    if k == 'irtifaya_cik':
        return adim['metre']
    if k == 'yuksel' and irtifa is not None:
        return irtifa + adim['metre']
    if k == 'alcal' and irtifa is not None:
        return max(0.0, irtifa - adim['metre'])
    if k == 'in':
        return 0.0
    if k == 'kalk':
        return adim.get('irtifa_m') or None      # varsayilan kalkis irtifasini yurutucu bilir
    if k == 'git_koordinat' and adim.get('irtifa_m'):
        return adim['irtifa_m']
    return irtifa


class YerCozucu:

    def __init__(self, saglayici, arama_yaricapi_m=3000.0, en_uzak_m=1000.0, seyir_irtifasi_m=30.0,
                 git_koordinata_seyir=True):
        self.saglayici = saglayici
        self.arama_yaricapi_m = arama_yaricapi_m
        self.en_uzak_m = en_uzak_m
        self.seyir_irtifasi_m = seyir_irtifasi_m
        self.git_koordinata_seyir = git_koordinata_seyir     # LLM'in dogrudan urettigi git_koordinat

    def gerekli_mi(self, adimlar):
        """Bu liste harita_node'da islenmeli mi? (Gerekmiyorsa komut beklemeden gecer.)"""
        if harita_adimi_var_mi(adimlar):
            return True
        return self._seyir_acik and self.git_koordinata_seyir and \
            any(a['komut'] == 'git_koordinat' for a in adimlar)

    @property
    def _seyir_acik(self):
        return self.seyir_irtifasi_m > 0

    def coz(self, adimlar, konum):
        yeni, mesajlar = [], []
        irtifa = konum.irtifa_m
        for adim in adimlar:
            haritadan = adim['komut'] in HARITA_KOMUTLARI
            if haritadan:
                try:
                    yer, aranan = self._bul(adim, konum)
                except HaritaHatasi as e:
                    return Cozum(mesajlar=mesajlar, hata=str(e))
                if yer is None:
                    return Cozum(mesajlar=mesajlar, hata=f'{mesafe_yaz(self.arama_yaricapi_m)} içinde '
                                                         f'{aranan} bulunamadı')
                if yer.mesafe_m > self.en_uzak_m:
                    return Cozum(mesajlar=mesajlar, hata=f'en yakın {aranan} ({yer.ad}) {mesafe_yaz(yer.mesafe_m)} '
                                                         f'uzakta; sınır {mesafe_yaz(self.en_uzak_m)}')
                mesajlar.append(f'{mesafe_yaz(yer.mesafe_m)} uzaktaki {yer.ad} için yola çıkıyorum')
                adim = {'komut': 'git_koordinat', 'enlem': yer.enlem, 'boylam': yer.boylam}
            if adim['komut'] == 'git_koordinat' and self._seyir_acik and \
                    (haritadan or self.git_koordinata_seyir):
                tirmanma = max(self.seyir_irtifasi_m, adim.get('irtifa_m') or 0.0)
                if irtifa is None or irtifa < tirmanma - 0.5:
                    yeni.append({'komut': 'irtifaya_cik', 'metre': float(tirmanma)})
                    irtifa = tirmanma
            yeni.append(adim)
            irtifa = irtifa_sonrasi(adim, irtifa)
        if not konum.gps and harita_adimi_var_mi(adimlar):
            mesajlar.append('GPS yok: arama kalkış noktasına göre yapıldı')
        return Cozum(adimlar=yeni, mesajlar=mesajlar)

    def _bul(self, adim, konum):
        if adim['komut'] == 'yakin_yere_git':
            aranan = tur_bilgisi(adim['tur'])['ad']
            yer = self.saglayici.en_yakin(adim['tur'], konum.enlem, konum.boylam, self.arama_yaricapi_m)
        else:
            aranan = adim['ad']
            yer = self.saglayici.ara(adim['ad'], konum.enlem, konum.boylam, self.arama_yaricapi_m)
        return yer, aranan
