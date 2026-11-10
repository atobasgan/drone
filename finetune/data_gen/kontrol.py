"""Uretilen her ornegin otomatik kontrolu (Gorev 4.1 / 4.2 KONTROL maddeleri).

Bir ornek ancak su durumda veri setine girer:
  1. Etiket semaya uyuyor (command_parser.schema.dogrula).
  2. Etiketteki her sayi normalize edilmis cumlede AYNEN geciyor. Tek istisna:
     derecesi soylenmeyen donusun varsayilan 90'i ("sağa dön").
  3. Komut cumlesinde etikette OLMAYAN sayi yok. Whisper "yere kon ve 60 m in" cumlesini
     "yere 10 ve 60 m in" yazabiliyor; bunu ogrenen model sayilari yok saymayi ogrenir.
  4. normalize iki kez uygulaninca degismiyor (komut_cozucu tekrar normalize eder).
  5. Cumle hizli yolun "acil" kuralina takilmiyor (dur haric): takilsa LLM'e hic gitmez.
"""
from ..ortak import dogrula, normalize, sayi


def _sayi_mi(token):
    try:
        float(token)
        return True
    except ValueError:
        return False


ACIL_KELIMELER = frozenset({'dur', 'durdur', 'stop', 'acil', 'iptal'})
SAYI_ALANLARI = ('metre', 'irtifa_m', 'derece', 'saniye', 'mps', 'enlem', 'boylam')


def sorun(norm_cumle, adimlar):
    """Sorun yoksa None, varsa kisa aciklama."""
    try:
        dogrula({'adimlar': adimlar})
    except ValueError as e:
        return f'sema: {e}'
    if normalize(norm_cumle) != norm_cumle:
        return 'normalize tekrar uygulaninca degisiyor'
    tokenler = set(norm_cumle.replace("'", ' ').split())
    for adim in adimlar:
        for alan in SAYI_ALANLARI:
            if alan not in adim:
                continue
            varsayilan = adim['komut'] == 'don' and alan == 'derece' and adim[alan] == 90 \
                and '°' not in tokenler
            if not varsayilan and str(sayi(adim[alan])) not in tokenler:
                return f'sayi cumlede yok: {alan}={adim[alan]}'
    komutlar = {a['komut'] for a in adimlar}
    if 'bilinmiyor' not in komutlar:
        etiketteki = {str(sayi(a[alan])) for a in adimlar for alan in SAYI_ALANLARI if alan in a}
        fazla = [t for t in tokenler if _sayi_mi(t) and t not in etiketteki]
        if fazla:
            return f'etikette olmayan sayi: {fazla[0]}'
    if 'dur' not in komutlar and not ACIL_KELIMELER.isdisjoint(norm_cumle.split()):
        return 'acil kelime var (LLM\'e gitmez)'
    return None
