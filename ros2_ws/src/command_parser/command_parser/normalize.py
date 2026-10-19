"""Metin normalizasyonu (Gorev 2.1, MIMARI.txt 3.6).

STT'den (ya da klavyeden) gelen metni tek bicime sokar:
  - Turkce kucuk harf (I -> ı, İ -> i), noktalama temizligi
  - yaziyla sayi -> rakam:  "beş yüz" -> 500, "bin iki yüz" -> 1200,
                            "bir buçuk" -> 1.5, "yüz elliye" -> "150'ye"
  - birimler: metre/mt/m -> "m", kilometre/km -> metreye cevrilir,
              derece -> "°", sn -> saniye
Sayilari LLM'e birakmiyoruz; burada kesin ceviriyoruz.

    >>> normalize("Beş Yüz Metre Yüksel!")
    '500 m yüksel'
"""
import re

BIRLER = {
    'sıfır': 0, 'bir': 1, 'iki': 2, 'üç': 3, 'dört': 4, 'beş': 5,
    'altı': 6, 'yedi': 7, 'sekiz': 8, 'dokuz': 9,
}
ONLAR = {
    'on': 10, 'yirmi': 20, 'otuz': 30, 'kırk': 40, 'elli': 50,
    'altmış': 60, 'yetmiş': 70, 'seksen': 80, 'doksan': 90,
}
CARPANLAR = {'yüz': 100, 'bin': 1000, 'milyon': 1000000}
SAYI_KELIMELERI = {**BIRLER, **ONLAR, **CARPANLAR}

# Ek almis sayi kelimeleri icin unsuz yumusamasi: "dörde", "buçuğa"
YUMUSAMA = {'dörd': 'dört', 'buçuğ': 'buçuk'}
# Yalnizca yon/yer ekleri: "yüze", "elliye", "ona", "bine", "yüzden"
EKLER = ('den', 'dan', 'ten', 'tan', 'ye', 'ya', 'de', 'da', 'te', 'ta', 'e', 'a')

BIRIM_DESENI = re.compile(r"^(metre|metro?|mt|m|meter)('?)(.*)$")
KM_DESENI = re.compile(r"^(kilometre|km)('?)(.*)$")
DERECE_DESENI = re.compile(r"^(derece|°)('?)(.*)$")
# Birim kelimesinin arkasina gelebilecek ekler ("metreye", "m'de", "metrelik")
BIRIM_EKLERI = {'', 'ye', 'ya', 'e', 'a', 'de', 'da', 'den', 'dan', 'lik', 'lık', 'yi', 'yı', 'si', 'sı'}
# "bir", "yarım" tek basina ancak arkasindan birim gelirse sayi sayilir ("bir şey" sayi degil)
_ZAMAN_DESENI = re.compile(r'^(saniye|sn|dakika|tur)\w*$')

_NOKTALAMA = re.compile(r"[^\w\s'.,°/-]")
_ONDALIK_VIRGUL = re.compile(r'(?<=\d),(?=\d)')
_RAKAM_BIRIM = re.compile(r"(?<=\d)((?:kilometre|metre|derece)\w*|mt|km|m|°)(?=\s|'|$)")
_APOSTROF = re.compile(r"[’‘`´]")


def tr_kucuk(metin):
    """Turkce kurallarina uygun kucuk harf."""
    return metin.replace('I', 'ı').replace('İ', 'i').lower()


def _sayi_yaz(deger):
    if abs(deger - round(deger)) < 1e-9:
        return str(int(round(deger)))
    return f'{deger:g}'


def _ekli_sayi(token):
    """'elliye' -> ('elli', 'ye'); ek yoksa ya da sayi degilse None."""
    for ek in EKLER:
        if token.endswith(ek) and len(token) > len(ek):
            kok = token[:-len(ek)].rstrip("'")
            kok = YUMUSAMA.get(kok, kok)
            if kok in SAYI_KELIMELERI or kok == 'buçuk':
                return kok, ek
    return None


def _birim_mi(token):
    for desen in (BIRIM_DESENI, KM_DESENI, DERECE_DESENI):
        m = desen.match(token)
        if m and m.group(3) in BIRIM_EKLERI:
            return True
    return _ZAMAN_DESENI.match(token) is not None


def _sayi_mi(token):
    return token in SAYI_KELIMELERI


def _rakam_mi(token):
    return re.fullmatch(r'\d+(\.\d+)?', token) is not None


class _Toplayici:
    """Turkce sayi kelimelerini soldan saga toplar: 'bin iki yüz elli' -> 1250."""

    def __init__(self):
        self.toplam = 0
        self.grup = 0
        self.buçuk = False

    def ekle(self, token):
        if _rakam_mi(token):
            self.grup += float(token)
        elif token in BIRLER or token in ONLAR:
            self.grup += SAYI_KELIMELERI[token]
        elif token == 'yüz':
            self.grup = (self.grup or 1) * 100
        elif token in ('bin', 'milyon'):
            self.toplam += (self.grup or 1) * CARPANLAR[token]
            self.grup = 0
        elif token == 'buçuk':
            self.buçuk = True

    def deger(self):
        return self.toplam + self.grup + (0.5 if self.buçuk else 0)


def _sayilari_cevir(tokenler):
    cikti = []
    i = 0
    n = len(tokenler)
    while i < n:
        tok = tokenler[i]
        sonraki = tokenler[i + 1] if i + 1 < n else ''

        # rakam + carpan: "5 yüz" -> 500
        baslar = _sayi_mi(tok) or (_rakam_mi(tok) and sonraki in CARPANLAR)
        ekli = None if baslar else _ekli_sayi(tok)
        if not baslar and not ekli:
            cikti.append(tok)
            i += 1
            continue

        # Tek basina "bir"/"on" gibi belirsiz kelimeler
        if tok == 'bir' and not (_sayi_mi(sonraki) or sonraki == 'buçuk' or _ekli_sayi(sonraki)
                                 or _birim_mi(sonraki)):
            cikti.append(tok)
            i += 1
            continue
        if ekli and tok == 'ona':      # "ona git" (zamir) sayi degil
            cikti.append(tok)
            i += 1
            continue

        top = _Toplayici()
        ek = ''
        while i < n:
            tok = tokenler[i]
            if _sayi_mi(tok) or (tok == 'buçuk' and not top.buçuk) or \
                    (_rakam_mi(tok) and top.deger() == 0 and i + 1 < n and tokenler[i + 1] in CARPANLAR):
                top.ekle(tok)
                i += 1
                continue
            parca = _ekli_sayi(tok)
            if parca:
                top.ekle(parca[0])
                ek = parca[1]
                i += 1
            break
        cikti.append(_sayi_yaz(top.deger()) + (f"'{ek}" if ek else ''))
    return cikti


def _yarim(tokenler):
    """'yarım metre' -> '0.5 metre'"""
    cikti = []
    for i, tok in enumerate(tokenler):
        sonraki = tokenler[i + 1] if i + 1 < len(tokenler) else ''
        if tok == 'yarım' and _birim_mi(sonraki):
            cikti.append('0.5')
        else:
            cikti.append(tok)
    return cikti


def _birimleri_cevir(tokenler):
    cikti = []
    for tok in tokenler:
        onceki = cikti[-1] if cikti else ''
        sayi_once = _rakam_mi(onceki)

        m = KM_DESENI.match(tok)
        if m and m.group(3) in BIRIM_EKLERI:
            ek = m.group(3)
            if sayi_once:
                cikti[-1] = _sayi_yaz(float(onceki) * 1000)
                cikti.append("m'" + ek if ek else 'm')
            else:
                cikti.append('km')
            continue

        m = BIRIM_DESENI.match(tok)
        # "m" tek harfi ve "metro" yalnizca bir sayinin arkasindaysa birimdir
        if m and m.group(3) in BIRIM_EKLERI and (sayi_once or m.group(1) in ('metre', 'meter')):
            ek = m.group(3)
            cikti.append("m'" + ek if ek else 'm')
            continue

        m = DERECE_DESENI.match(tok)
        if m and m.group(3) in BIRIM_EKLERI:
            cikti.append('°')
            continue

        if tok == 'sn':
            cikti.append('saniye')
            continue
        cikti.append(tok)
    return cikti


def normalize(metin):
    """Ham metni normalize eder (bkz. modul aciklamasi)."""
    if not metin:
        return ''
    s = tr_kucuk(metin)
    s = _APOSTROF.sub("'", s)
    s = _ONDALIK_VIRGUL.sub('.', s)
    s = _NOKTALAMA.sub(' ', s)
    s = _RAKAM_BIRIM.sub(r' \1', s)
    s = s.replace('°', ' ° ')
    # rakam arasindaki nokta disindaki noktalar, virguller ve tireler bosluk olur
    s = re.sub(r'(?<!\d)\.|\.(?!\d)', ' ', s)
    s = re.sub(r'[,/-]', ' ', s)
    tokenler = [t.strip("'") for t in s.split()]
    tokenler = [t for t in tokenler if t]
    tokenler = _yarim(tokenler)
    tokenler = _sayilari_cevir(tokenler)
    tokenler = _birimleri_cevir(tokenler)
    return ' '.join(tokenler)
