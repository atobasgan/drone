"""Hizli yol: sik ve basit komutlari LLM'siz, < 5 ms'de cozer (Gorev 2.2).

Girdi normalize() edilmis metindir ("500 m yüksel", "sağa 90 ° dön").
Cikti, LLM ile ayni bicimdedir (schema.py): {"adimlar": [{"komut": ...}]}.
Kural: Hizli yol DAR ve KESIN olmali. Desenler cumlenin TAMAMINA uymalidir
(fullmatch); suphede kalirsan None dondur, cumle LLM'e gitsin.
"""
import re

ACIL_KELIMELER = frozenset({'dur', 'durdur', 'stop', 'acil', 'iptal'})

# Cumlenin basinda/sonunda anlam degistirmeyen dolgu kelimeleri
DOLGU = frozenset({'lütfen', 'hemen', 'şimdi', 'hadi', 'drone', 'tamam', 'haydi'})

N = r'(\d+(?:\.\d+)?)'
DUNYA = {'kuzeye': 'kuzey', 'güneye': 'guney', 'doğuya': 'dogu', 'batıya': 'bati'}
GOVDE = {'ileri': 'ileri', 'geri': 'geri', 'sağa': 'sag', 'sola': 'sol'}
DUNYA_RE = '(' + '|'.join(DUNYA) + ')'
GOVDE_RE = '(' + '|'.join(GOVDE) + ')'
YON_RE = '(' + '|'.join(list(DUNYA) + list(GOVDE)) + ')'
YONLER = {**DUNYA, **GOVDE}

GIT = r'(?: (?:git|ilerle|uç))?'
YUKSEL = r'(?:yüksel|yukarı çık|tırman|yukarı)'
ALCAL = r'(?:alçal|aşağı in|aşağı|in)'
YONELME = r"m'(?:ye|ya|e|a)"


def _adim(**kw):
    return {'adimlar': [kw]}


def _m(g):
    return float(g)


# (desen, eslesme -> komut) ciftleri; sirasi onemli degil, hepsi fullmatch.
_KURALLAR = [
    # kalk
    (r'(?:kalk|kalkış yap|havalan|kalkışa geç|uçuşa başla)',
     lambda m: _adim(komut='kalk')),
    (rf'{N} {YONELME} (?:kalk|havalan|kalkış yap)',
     lambda m: _adim(komut='kalk', irtifa_m=_m(m[1]))),
    # in
    (r'(?:in|iniş yap|yere in|inişe geç|aşağı in ve dur)',
     lambda m: _adim(komut='in')),
    # yuksel (goreli)
    (rf'{N} m {YUKSEL}', lambda m: _adim(komut='yuksel', metre=_m(m[1]))),
    (rf'yukarı {N} m(?: çık)?', lambda m: _adim(komut='yuksel', metre=_m(m[1]))),
    (rf'irtifayı {N} m artır', lambda m: _adim(komut='yuksel', metre=_m(m[1]))),
    # alcal (goreli)
    (rf'{N} m {ALCAL}', lambda m: _adim(komut='alcal', metre=_m(m[1]))),
    (rf'aşağı {N} m(?: in)?', lambda m: _adim(komut='alcal', metre=_m(m[1]))),
    (rf'irtifayı {N} m azalt', lambda m: _adim(komut='alcal', metre=_m(m[1]))),
    # irtifaya_cik (mutlak): "500 m'ye çık", "irtifayı 100 m'ye getir"
    (rf'{N} {YONELME} (?:çık|yüksel|alçal|in|tırman)',
     lambda m: _adim(komut='irtifaya_cik', metre=_m(m[1]))),
    (rf"irtifayı {N} (?:{YONELME}|m) (?:çıkar|yap|ayarla|getir)",
     lambda m: _adim(komut='irtifaya_cik', metre=_m(m[1]))),
    (rf'{N} m irtifaya (?:çık|git|yüksel)',
     lambda m: _adim(komut='irtifaya_cik', metre=_m(m[1]))),
    # git_yon
    (rf'{YON_RE} {N} m{GIT}',
     lambda m: _adim(komut='git_yon', yon=YONLER[m[1]], metre=_m(m[2]))),
    (rf'{N} m {YON_RE}{GIT}',
     lambda m: _adim(komut='git_yon', yon=YONLER[m[2]], metre=_m(m[1]))),
    # don
    (rf'(sağa|sola) {N} ° dön',
     lambda m: _adim(komut='don', yon=GOVDE[m[1]], derece=_m(m[2]))),
    (rf'{N} ° (sağa|sola) dön',
     lambda m: _adim(komut='don', yon=GOVDE[m[2]], derece=_m(m[1]))),
    (r'(sağa|sola) dön',
     lambda m: _adim(komut='don', yon=GOVDE[m[1]], derece=90.0)),
    # eve_don
    (r'(?:eve dön|eve git|üsse dön|kalkış noktasına dön|başlangıç noktasına dön|eve geri dön)',
     lambda m: _adim(komut='eve_don')),
    # bekle
    (rf'{N} saniye bekle', lambda m: _adim(komut='bekle', saniye=_m(m[1]))),
    # hiz_ayarla: normalize "m/s"yi "m s" yapar
    (rf'hızı {N}(?: m s| m saniye)? (?:yap|ayarla)',
     lambda m: _adim(komut='hiz_ayarla', mps=_m(m[1]))),
]
_DERLENMIS = [(re.compile(desen), uret) for desen, uret in _KURALLAR]


def acil_mi(metin):
    """Cumlede acil kelime varsa True. LLM'e hic ugramadan DUR uygulanir."""
    return not ACIL_KELIMELER.isdisjoint(metin.split())


def _dolgu_temizle(metin):
    tokenler = metin.split()
    while tokenler and tokenler[0] in DOLGU:
        tokenler.pop(0)
    while tokenler and tokenler[-1] in DOLGU:
        tokenler.pop()
    return ' '.join(tokenler)


def coz(metin):
    """Normalize metni komut sozlugune cevirir; eslesmezse None (LLM'e gider)."""
    if acil_mi(metin):
        return _adim(komut='dur')
    temiz = _dolgu_temizle(metin)
    for desen, uret in _DERLENMIS:
        m = desen.fullmatch(temiz)
        if m:
            return uret(m)
    return None
