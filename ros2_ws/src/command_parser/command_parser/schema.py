"""LLM <-> drone sozlesmesi: komut JSON semasi (MIMARI.txt Bolum 4).

Ayni sema hem llama-server'a kisit olarak verilir (cikti %100 gecerli JSON),
hem de gelen cevabi Python tarafinda dogrulamak icin kullanilir.
"""

YONLER = ['ileri', 'geri', 'sag', 'sol', 'kuzey', 'guney', 'dogu', 'bati']
DON_YONLERI = ['sag', 'sol']
YER_TURLERI = ['hastane', 'eczane', 'benzinlik', 'polis', 'itfaiye', 'okul', 'park', 'market']

# komut -> (zorunlu alanlar, istege bagli alanlar); alan -> JSON tipi
SAYI = {'type': 'number'}
ALANLAR = {
    'metre': SAYI,
    'irtifa_m': SAYI,
    'derece': SAYI,
    'enlem': SAYI,
    'boylam': SAYI,
    'saniye': SAYI,
    'mps': SAYI,
    'yon': {'type': 'string', 'enum': YONLER},
    'tur': {'type': 'string', 'enum': YER_TURLERI},
}
KOMUTLAR = {
    'kalk': ((), ('irtifa_m',)),
    'in': ((), ()),
    'yuksel': (('metre',), ()),
    'alcal': (('metre',), ()),
    'irtifaya_cik': (('metre',), ()),
    'git_yon': (('yon', 'metre'), ()),
    'don': (('yon', 'derece'), ()),
    'git_koordinat': (('enlem', 'boylam'), ('irtifa_m',)),
    'yakin_yere_git': (('tur',), ()),
    'bekle': (('saniye',), ()),
    'hiz_ayarla': (('mps',), ()),
    'eve_don': ((), ()),
    'dur': ((), ()),
    'bilinmiyor': ((), ()),
}
MAX_ADIM = 5


def _komut_semasi(ad, zorunlu, istege_bagli):
    ozellikler = {'komut': {'const': ad}}
    for alan in zorunlu + istege_bagli:
        ozellikler[alan] = dict(ALANLAR[alan])
    if ad == 'don':
        ozellikler['yon'] = {'type': 'string', 'enum': DON_YONLERI}
    return {
        'type': 'object',
        'properties': ozellikler,
        'required': ['komut', *zorunlu],
        'additionalProperties': False,
    }


KOMUT_SEMASI = {
    'type': 'object',
    'properties': {
        'adimlar': {
            'type': 'array',
            'items': {'anyOf': [_komut_semasi(ad, *a) for ad, a in KOMUTLAR.items()]},
            'minItems': 1,
            'maxItems': MAX_ADIM,
        },
    },
    'required': ['adimlar'],
    'additionalProperties': False,
}


class SemaHatasi(ValueError):
    pass


def dogrula(veri):
    """Semaya uygunlugu kontrol eder, sayilari float'a cevirir; adim listesi dondurur.

    llama-server sema kisitini uyguladigi icin normalde hata cikmaz; bu kontrol
    kisit desteklenmeyen bir sunucuya ya da bozuk cevaba karsi emniyettir.
    """
    if not isinstance(veri, dict) or not isinstance(veri.get('adimlar'), list):
        raise SemaHatasi('"adimlar" listesi yok')
    adimlar = veri['adimlar']
    if not 1 <= len(adimlar) <= MAX_ADIM:
        raise SemaHatasi(f'adim sayisi 1-{MAX_ADIM} olmali')
    temiz = []
    for adim in adimlar:
        if not isinstance(adim, dict) or adim.get('komut') not in KOMUTLAR:
            raise SemaHatasi(f'bilinmeyen komut: {adim!r}')
        ad = adim['komut']
        zorunlu, istege_bagli = KOMUTLAR[ad]
        izinli = {'komut', *zorunlu, *istege_bagli}
        fazla = set(adim) - izinli
        if fazla:
            raise SemaHatasi(f'{ad}: beklenmeyen alan {sorted(fazla)}')
        yeni = {'komut': ad}
        for alan in zorunlu + istege_bagli:
            if alan not in adim:
                if alan in zorunlu:
                    raise SemaHatasi(f'{ad}: "{alan}" eksik')
                continue
            deger = adim[alan]
            if ALANLAR[alan]['type'] == 'number':
                if isinstance(deger, bool) or not isinstance(deger, (int, float)):
                    raise SemaHatasi(f'{ad}.{alan} sayi degil')
                deger = float(deger)
            else:
                gecerli = DON_YONLERI if (ad == 'don' and alan == 'yon') else ALANLAR[alan]['enum']
                if deger not in gecerli:
                    raise SemaHatasi(f'{ad}.{alan} gecersiz: {deger!r}')
            yeni[alan] = deger
        temiz.append(yeni)
    return temiz


def bilinmiyor_mu(adimlar):
    """Herhangi bir adim 'bilinmiyor' ise tum cumle anlasilmamis sayilir (temkinli)."""
    return any(a['komut'] == 'bilinmiyor' for a in adimlar)


def msg_alanlarina(adim):
    """Sema bicimindeki adimi DroneCommand alanlarina cevirir (irtifa_m -> metre)."""
    alanlar = dict(adim)
    if 'irtifa_m' in alanlar:
        alanlar['metre'] = alanlar.pop('irtifa_m')
    return alanlar


def kanonik(adimlar):
    """Karsilastirma icin: sirali anahtarlar, yuvarlanmis sayilar."""
    return [
        tuple(sorted((k, round(v, 3) if isinstance(v, float) else v) for k, v in a.items()))
        for a in adimlar
    ]
