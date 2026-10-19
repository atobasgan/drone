"""Komut -> hedef eslemesi (MIMARI.txt 3.9). ROS'tan bagimsiz.

Komutlar, DroneCommand mesajinin alanlariyla ayni anahtarlara sahip
sozluklerdir: {'komut': 'yuksel', 'metre': 50.0, ...}.
"""
from dataclasses import dataclass, replace
import math

from . import geo

KOMUTLAR = (
    'kalk', 'in', 'yuksel', 'alcal', 'irtifaya_cik', 'git_yon', 'don',
    'git_koordinat', 'yakin_yere_git', 'bekle', 'hiz_ayarla', 'eve_don', 'dur',
)
HAREKET_KOMUTLARI = ('kalk', 'yuksel', 'alcal', 'irtifaya_cik', 'git_yon', 'don',
                     'git_koordinat', 'yakin_yere_git')
GIT_YONLERI = tuple(geo.DUNYA_YONLERI) + tuple(geo.GOVDE_YONLERI)
DON_YONLERI = ('sag', 'sol')


class KomutHatasi(ValueError):
    """Komut hedefe cevrilemedi; mesaji kullaniciya gosterilir."""


@dataclass(frozen=True)
class Poz:
    """NED konum + yaw."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0

    @property
    def irtifa(self):
        return -self.z


@dataclass(frozen=True)
class Hedef:
    """Bir komutun yurutucude ne yapacagi.

    tip:
      konum   -> poz'a git (offboard konum setpoint'i)
      in      -> VEHICLE_CMD_NAV_LAND
      eve_don -> VEHICLE_CMD_NAV_RETURN_TO_LAUNCH
      bekle   -> poz'da 'saniye' kadar asili kal
      hiz     -> yatay/dikey hiz sinirini 'mps' yap (aninda biter)
      dur     -> mevcut konumda asili kal (aninda biter)
    """
    tip: str
    poz: Poz
    saniye: float = 0.0
    mps: float = 0.0


def _f(komut, anahtar):
    deger = komut.get(anahtar)
    return float(deger) if deger is not None else 0.0


def hedef_hesapla(komut, baz, varsayilan_irtifa=10.0, ref_latlon=None):
    """Komutu, 'baz' pozuna gore bir Hedef'e cevirir.

    baz: komut baslarken kullanilacak referans (havadayken son hedef, yerdeyken
         mevcut konum).
    ref_latlon: (ref_lat, ref_lon) yerel NED cercevesinin orijini; git_koordinat
         icin gerekli (VehicleLocalPosition.ref_lat/ref_lon).
    """
    ad = komut.get('komut', '')
    m = _f(komut, 'metre')

    if ad == 'kalk':
        irtifa = m if m > 0 else varsayilan_irtifa
        return Hedef('konum', replace(baz, z=-irtifa))
    if ad == 'yuksel':
        return Hedef('konum', replace(baz, z=baz.z - m))
    if ad == 'alcal':
        return Hedef('konum', replace(baz, z=baz.z + m))
    if ad == 'irtifaya_cik':
        return Hedef('konum', replace(baz, z=-m))
    if ad == 'git_yon':
        yon = komut.get('yon', '')
        if yon not in GIT_YONLERI:
            raise KomutHatasi(f'"{yon}" geçerli bir yön değil')
        dx, dy = geo.yon_to_ned(yon, m, baz.yaw)
        return Hedef('konum', replace(baz, x=baz.x + dx, y=baz.y + dy))
    if ad == 'don':
        yon = komut.get('yon', '')
        if yon not in DON_YONLERI:
            raise KomutHatasi(f'dönüş yönü "{yon}" geçersiz (sag/sol)')
        derece = _f(komut, 'derece')
        isaret = 1.0 if yon == 'sag' else -1.0
        return Hedef('konum', replace(baz, yaw=geo.aci_sar(baz.yaw + isaret * math.radians(derece))))
    if ad == 'git_koordinat':
        if ref_latlon is None:
            raise KomutHatasi('konum referansı (GPS) henüz yok')
        x, y = geo.enlem_boylam_to_ned(_f(komut, 'enlem'), _f(komut, 'boylam'), *ref_latlon)
        z = -m if m > 0 else baz.z
        return Hedef('konum', replace(baz, x=x, y=y, z=z))
    if ad == 'bekle':
        return Hedef('bekle', baz, saniye=_f(komut, 'saniye'))
    if ad == 'hiz_ayarla':
        return Hedef('hiz', baz, mps=_f(komut, 'mps'))
    if ad == 'dur':
        return Hedef('dur', baz)
    if ad == 'in':
        return Hedef('in', replace(baz, z=0.0))
    if ad == 'eve_don':
        return Hedef('eve_don', Poz(0.0, 0.0, 0.0, baz.yaw))
    if ad == 'yakin_yere_git':
        raise KomutHatasi('harita komutları henüz desteklenmiyor (Faz 5)')
    raise KomutHatasi(f'bilinmeyen komut: "{ad}"')
