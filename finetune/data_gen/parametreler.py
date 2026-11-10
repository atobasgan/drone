"""Rastgele komut parametreleri ve Turkce sayi yazimi.

Sablonlardaki {metre}, {yon} gibi bosluklar buradaki fonksiyonlarla doldurulur.
Her doldurma iki sey dondurur: CUMLEDE yazilacak bicim ve ETIKETE girecek deger.
    >>> rng = random.Random(0); metre(rng)
    ('elli', 50)            # ya da ('50', 50); sayi bazen rakamla, bazen yaziyla
"""
import random

# --- sayilarin yaziyla yazilmasi (STT sayilari cogu zaman yaziyla verir) ---------
_BIRLER = ['', 'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz']
_ONLAR = ['', 'on', 'yirmi', 'otuz', 'kırk', 'elli', 'altmış', 'yetmiş', 'seksen', 'doksan']


def sayi_yaziyla(sayi):
    """1234 -> 'bin iki yüz otuz dört', 2.5 -> 'iki buçuk'. 0-9999 arasi."""
    if sayi != int(sayi):
        tam = int(sayi)
        if sayi - tam == 0.5:
            return f'{sayi_yaziyla(tam)} buçuk' if tam else 'yarım'
        return str(sayi)                       # 1.25 gibi: rakamla birak
    n = int(sayi)
    if n == 0:
        return 'sıfır'
    parcalar = []
    binler, n = divmod(n, 1000)
    if binler:
        parcalar.append('bin' if binler == 1 else f'{_BIRLER[binler]} bin')
    yuzler, n = divmod(n, 100)
    if yuzler:
        parcalar.append('yüz' if yuzler == 1 else f'{_BIRLER[yuzler]} yüz')
    onlar, birler = divmod(n, 10)
    if onlar:
        parcalar.append(_ONLAR[onlar])
    if birler:
        parcalar.append(_BIRLER[birler])
    return ' '.join(parcalar)


def sayi_bicimi(rng, sayi, yaziyla_orani=0.5):
    """Cumleye yazilacak bicim: '50' ya da 'elli'. Ondalik: '2.5' / '2,5' / 'iki buçuk'."""
    if rng.random() < yaziyla_orani:
        return sayi_yaziyla(sayi)
    if sayi == int(sayi):
        return str(int(sayi))
    return str(sayi).replace('.', ',') if rng.random() < 0.3 else str(sayi)


def _sec(rng, yaygin, aralik, yaygin_orani=0.7):
    """Gercek konusmada yuvarlak sayilar cok daha sik: %70 listeden, %30 araliktan."""
    if rng.random() < yaygin_orani:
        return rng.choice(yaygin)
    return rng.randint(*aralik)


# --- parametre ureticileri: (cumle_bicimi, etiket_degeri) ------------------------
def metre(rng):
    deger = _sec(rng, [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100, 120, 150,
                       200, 250, 300, 400, 500, 1000], (1, 600))
    if rng.random() < 0.05:
        deger = rng.choice([0.5, 1.5, 2.5, 3.5, 7.5, 12.5])
    return sayi_bicimi(rng, deger), deger


def irtifa(rng):
    """Kalkis / mutlak irtifa: drone icin makul 5-150 m."""
    deger = _sec(rng, [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 100, 120, 150], (3, 150))
    return sayi_bicimi(rng, deger), deger


def derece(rng):
    deger = _sec(rng, [10, 15, 20, 30, 45, 60, 90, 120, 135, 180, 270, 360], (5, 359))
    return sayi_bicimi(rng, deger), deger


def saniye(rng):
    deger = _sec(rng, [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120], (1, 300))
    return sayi_bicimi(rng, deger), deger


def dakika(rng):
    """Cumlede dakika, etikette saniye (normalize "2 dakika" -> "120 saniye" yapar)."""
    deger = rng.choice([1, 2, 3, 5, 10, 1.5, 2.5, 0.5])
    return sayi_bicimi(rng, deger), deger * 60


def mps(rng):
    deger = _sec(rng, [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 2.5, 1.5], (1, 15))
    return sayi_bicimi(rng, deger), deger


def kmsaat(rng):
    """Cumlede km/saat, etikette m/s (normalize cevirir, 2 basamak yuvarlar)."""
    deger = rng.choice([9, 18, 36, 54, 10, 20, 30, 40, 50])
    return sayi_bicimi(rng, deger, yaziyla_orani=0.4), round(deger / 3.6, 2)


def koordinat(rng):
    """Turkiye civari enlem/boylam; ondalik oldugu icin hep rakamla."""
    enlem = round(rng.uniform(36.0, 42.0), rng.choice([4, 5, 6]))
    boylam = round(rng.uniform(26.0, 45.0), rng.choice([4, 5, 6]))
    return (str(enlem), enlem), (str(boylam), boylam)


# --- yonler ve yerler -------------------------------------------------------------
# etiket -> yonelme hali ("kuzeye"), ad hali ("kuzey"), "tarafa" icin ad
YONLER = {
    'kuzey': ('kuzeye', 'kuzey'),
    'guney': ('güneye', 'güney'),
    'dogu': ('doğuya', 'doğu'),
    'bati': ('batıya', 'batı'),
    'sag': ('sağa', 'sağ'),
    'sol': ('sola', 'sol'),
    'ileri': ('ileri', 'ön'),
    'geri': ('geri', 'arka'),
}
DUNYA_YONLERI = ['kuzey', 'guney', 'dogu', 'bati']
GOVDE_YONLERI = ['ileri', 'geri', 'sag', 'sol']

# etiket -> cumlede yonelme halleri ("hastaneye", "en yakin X'e")
YERLER = {
    'hastane': ['hastaneye'],
    'eczane': ['eczaneye'],
    'benzinlik': ['benzinliğe', 'akaryakıt istasyonuna'],
    'polis': ['polis merkezine', 'karakola'],
    'itfaiye': ['itfaiyeye', 'itfaiye istasyonuna'],
    'okul': ['okula'],
    'park': ['parka'],
    'market': ['markete'],
}


def yon(rng, kume=None):
    """(yonelme, ad, etiket): ('kuzeye', 'kuzey', 'kuzey')."""
    etiket = rng.choice(kume or list(YONLER))
    yonelme, ad = YONLER[etiket]
    return yonelme, ad, etiket


def yer(rng):
    etiket = rng.choice(list(YERLER))
    return rng.choice(YERLER[etiket]), etiket


def yeni_rng(tohum):
    return random.Random(tohum)
