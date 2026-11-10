"""Gorev 4.6: yanlis ornekleri hata turlerine ayirir (hangi turden veri eklenmeli?).

  negatifi_kabul : komut degilken komut uretti (en tehlikelisi: yanlis kabul)
  komutu_kacirdi : komut varken "bilinmiyor" dedi ya da cevap uretemedi
  adim_sayisi    : cok adimli cumlede eksik / fazla adim
  goreli_mutlak  : yuksel/alcal <-> irtifaya_cik karisikligi
  komut_yanlis   : baska bir komut
  sayi           : komut dogru, sayi yanlis (ya da baska adima kaymis)
  yon            : komut dogru, yon / yer turu yanlis
"""
from collections import Counter

GORELI_MUTLAK = {'yuksel', 'alcal', 'irtifaya_cik'}


def hata_turu(beklenen, uretilen):
    beklenen_bos = any(a['komut'] == 'bilinmiyor' for a in beklenen)
    if beklenen_bos:
        return 'negatifi_kabul' if uretilen else None
    if not uretilen:
        return 'komutu_kacirdi'
    if len(beklenen) != len(uretilen):
        return 'adim_sayisi'
    for b, u in zip(beklenen, uretilen):
        if b['komut'] != u['komut']:
            if {b['komut'], u['komut']} <= GORELI_MUTLAK:
                return 'goreli_mutlak'
            return 'komut_yanlis'
    for b, u in zip(beklenen, uretilen):
        for alan in set(b) | set(u):
            if b.get(alan) != u.get(alan):
                return 'yon' if alan in ('yon', 'tur') else 'sayi'
    return None


def ozet(hatalar):
    """hatalar: degerlendir()'in 'hatalar' listesi -> Counter(tur)."""
    return Counter(hata_turu(beklenen, uretilen) or 'diger'
                   for _, _, beklenen, uretilen, _, _ in hatalar)
