"""Guvenlik katmani: hatali/tehlikeli komutu drone'a ulasmadan durdurur.

Limitler YAML parametre dosyasindan gelir (drone_bringup/config/guvenlik.yaml).
ROS'tan bagimsizdir; executor_node bunu kullanir.
"""
from dataclasses import dataclass, replace
import math

from .planlayici import (
    DON_YONLERI, GIT_YONLERI, HAREKET_KOMUTLARI, KOMUTLAR,
    KomutHatasi, Poz, hedef_hesapla,
)


@dataclass(frozen=True)
class Limitler:
    max_irtifa: float = 120.0          # m, yerden
    min_irtifa: float = 2.0            # m, havadayken inilebilecek en alt (in haric)
    max_adim_mesafe: float = 1000.0    # m, tek komutta 3B yer degistirme
    geofence_yaricap: float = 1500.0   # m, kalkis noktasindan yatay
    min_batarya: float = 0.25          # 0..1; altinda yeni hareket kabul edilmez
    max_bekle_saniye: float = 300.0
    max_hiz: float = 15.0              # m/s, hiz_ayarla ust siniri
    varsayilan_kalkis_irtifa: float = 10.0


@dataclass(frozen=True)
class AracDurumu:
    """Kontrol aninda aracin durumu."""
    poz: Poz
    havada: bool
    batarya: float = 1.0               # 0..1 (bilinmiyorsa 1)
    ref_latlon: tuple = None


class Reddedildi(Exception):
    """Komut guvenlik kontrolunden gecemedi; mesaj kullaniciya soylenir."""


def _sayi(komut, anahtar):
    deger = komut.get(anahtar)
    if deger is None:
        return None
    try:
        deger = float(deger)
    except (TypeError, ValueError):
        return None
    return deger if math.isfinite(deger) else None


class Guvenlik:
    def __init__(self, limitler=None):
        self.limitler = limitler or Limitler()

    # -- parametre kontrolleri -------------------------------------------
    def _parametreler(self, komut):
        ad = komut.get('komut')
        L = self.limitler
        if ad not in KOMUTLAR:
            raise Reddedildi(f'bilinmeyen komut: "{ad}"')

        if ad in ('yuksel', 'alcal', 'irtifaya_cik', 'git_yon'):
            m = _sayi(komut, 'metre')
            if m is None or m <= 0:
                raise Reddedildi(f'{ad}: mesafe eksik ya da pozitif değil')
        if ad == 'kalk':
            m = _sayi(komut, 'metre')
            if m is not None and m < 0:
                raise Reddedildi('kalk: irtifa negatif olamaz')
        if ad == 'git_yon' and komut.get('yon') not in GIT_YONLERI:
            raise Reddedildi(f'git_yon: geçersiz yön "{komut.get("yon")}"')
        if ad == 'don':
            if komut.get('yon') not in DON_YONLERI:
                raise Reddedildi(f'don: geçersiz yön "{komut.get("yon")}"')
            d = _sayi(komut, 'derece')
            if d is None or d <= 0 or d > 360:
                raise Reddedildi('don: derece 0-360 aralığında olmalı')
        if ad == 'bekle':
            s = _sayi(komut, 'saniye')
            if s is None or s <= 0 or s > L.max_bekle_saniye:
                raise Reddedildi(f'bekle: süre 0-{L.max_bekle_saniye:g} sn olmalı')
        if ad == 'hiz_ayarla':
            v = _sayi(komut, 'mps')
            if v is None or v <= 0 or v > L.max_hiz:
                raise Reddedildi(f'hiz_ayarla: hız 0-{L.max_hiz:g} m/s olmalı')
        if ad == 'git_koordinat':
            lat, lon = _sayi(komut, 'enlem'), _sayi(komut, 'boylam')
            if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180) \
                    or (lat == 0 and lon == 0):
                raise Reddedildi('git_koordinat: enlem/boylam geçersiz')
            m = _sayi(komut, 'metre')
            if m is not None and m < 0:
                raise Reddedildi('git_koordinat: irtifa negatif olamaz')

    # -- durum kontrolleri -------------------------------------------------
    def _durum(self, komut, durum):
        ad = komut['komut']
        if not durum.havada:
            if ad in ('in', 'eve_don'):
                raise Reddedildi('zaten yerdeyim')
            if ad in HAREKET_KOMUTLARI and ad != 'kalk':
                raise Reddedildi('yerdeyim, önce kalkış yapmalıyım')
        elif ad == 'kalk':
            raise Reddedildi('zaten havadayım')
        if ad in HAREKET_KOMUTLARI and durum.batarya < self.limitler.min_batarya:
            raise Reddedildi(
                f'batarya düşük (%{durum.batarya * 100:.0f}); sadece in / eve dön kabul edilir')

    # -- hedef kontrolleri -------------------------------------------------
    def _hedef(self, komut, durum, hedef):
        L = self.limitler
        if hedef.tip != 'konum':
            return
        p, b = hedef.poz, durum.poz
        if p.irtifa > L.max_irtifa:
            raise Reddedildi(f'hedef irtifa {p.irtifa:.0f} m, sınır {L.max_irtifa:.0f} m')
        if p.irtifa < L.min_irtifa:
            raise Reddedildi(f'hedef irtifa {p.irtifa:.0f} m çok alçak; inmek için "in" de')
        mesafe = math.dist((p.x, p.y, p.z), (b.x, b.y, b.z))
        if mesafe > L.max_adim_mesafe:
            raise Reddedildi(f'tek adımda {mesafe:.0f} m, sınır {L.max_adim_mesafe:.0f} m')
        uzaklik = math.hypot(p.x, p.y)
        if uzaklik > L.geofence_yaricap:
            raise Reddedildi(
                f'hedef kalkış noktasına {uzaklik:.0f} m, geofence {L.geofence_yaricap:.0f} m')

    # -- disariya acik ------------------------------------------------------
    def kontrol_et(self, komut, durum):
        """Tek komutu kontrol eder. Gecerse Hedef dondurur, gecmezse Reddedildi firlatir."""
        self._parametreler(komut)
        self._durum(komut, durum)
        try:
            hedef = hedef_hesapla(komut, durum.poz, self.limitler.varsayilan_kalkis_irtifa,
                                  durum.ref_latlon)
        except KomutHatasi as e:
            raise Reddedildi(str(e)) from e
        self._hedef(komut, durum, hedef)
        return hedef

    def liste_kontrol_et(self, komutlar, durum):
        """Cok adimli listeyi bastan sona benzeterek kontrol eder.

        Herhangi bir adim reddedilirse hicbiri yurutulmez. Reddedilirse
        Reddedildi('adim N: sebep') firlatir; gecerse hedef listesini dondurur.
        """
        hedefler = []
        for i, komut in enumerate(komutlar, 1):
            try:
                hedef = self.kontrol_et(komut, durum)
            except Reddedildi as e:
                onek = f'adım {i}: ' if len(komutlar) > 1 else ''
                raise Reddedildi(f'{onek}{e}') from e
            hedefler.append(hedef)
            durum = self.sonraki_durum(durum, hedef)
        return hedefler

    @staticmethod
    def sonraki_durum(durum, hedef):
        """Hedef tamamlandiktan sonraki tahmini durum."""
        if hedef.tip == 'konum':
            return replace(durum, poz=hedef.poz, havada=True)
        if hedef.tip in ('in', 'eve_don'):
            return replace(durum, poz=hedef.poz, havada=False)
        return durum
