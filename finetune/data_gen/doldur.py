"""Sablonu doldurur: "{yon} {metre} metre git" -> ("kuzeye elli metre git", adim).

Etiket burada, kodla kurulur; cumleyle ayni rastgele degerden geldigi icin hatasizdir.
"""
import re

from . import parametreler as p

_BOSLUK = re.compile(r'\{(\w+)\}')


def bosluklar(sablon):
    return _BOSLUK.findall(sablon)


def doldur(rng, sablon, komut):
    """(cumle, adim) dondurur. adim sema bicimindedir: {"komut": ..., alanlar...}."""
    adim = {'komut': komut}
    degerler = {}
    for ad in bosluklar(sablon):
        if ad in ('metre',):
            degerler[ad], adim['metre'] = p.metre(rng)
        elif ad == 'irtifa':
            alan = 'irtifa_m' if komut in ('kalk', 'git_koordinat') else 'metre'
            degerler[ad], adim[alan] = p.irtifa(rng)
        elif ad == 'derece':
            degerler[ad], adim['derece'] = p.derece(rng)
        elif ad == 'saniye':
            degerler[ad], adim['saniye'] = p.saniye(rng)
        elif ad == 'dakika':
            degerler[ad], adim['saniye'] = p.dakika(rng)
        elif ad == 'mps':
            degerler[ad], adim['mps'] = p.mps(rng)
        elif ad == 'kmsaat':
            degerler[ad], adim['mps'] = p.kmsaat(rng)
        elif ad in ('yon', 'taraf'):
            yonelme, isim, adim['yon'] = p.yon(rng)
            degerler[ad] = yonelme if ad == 'yon' else isim
        elif ad == 'dunya':
            _, degerler[ad], adim['yon'] = p.yon(rng, p.DUNYA_YONLERI)
        elif ad in ('sagsol', 'sagsol_ad'):
            yonelme, isim, adim['yon'] = p.yon(rng, ['sag', 'sol'])
            degerler[ad] = yonelme if ad == 'sagsol' else isim
        elif ad == 'yer':
            degerler[ad], adim['tur'] = p.yer(rng)
        elif ad in ('enlem', 'boylam'):
            if 'enlem' not in adim:
                (degerler['enlem'], adim['enlem']), (degerler['boylam'], adim['boylam']) = p.koordinat(rng)
        else:
            raise ValueError(f'bilinmeyen bosluk {{{ad}}}: {sablon}')
    if komut == 'don' and 'derece' not in adim:
        adim['derece'] = 90                     # derecesi soylenmeyen donus
    cumle = sablon.format(**degerler)
    return cumle, _sema_sirasi(adim)


def _sema_sirasi(adim):
    """Anahtar sirasi sabit olsun (model hep ayni sirayi ogrensin): komut, sonra semadaki sira."""
    sira = ['komut', 'yon', 'metre', 'irtifa_m', 'derece', 'enlem', 'boylam', 'tur', 'saniye', 'mps']
    return {k: adim[k] for k in sira if k in adim}
