"""Faz 5 harita komutlari: mevcut parser'i DEGISTIRMEDEN genisletir.

  yakin_yere_git {tur}  zaten semada vardi (Faz 2). Burada yalnizca hizli yol kalibi eklenir:
                        "en yakın hastaneye git" LLM'e gitmeden < 1 ms'de cozulur (Gorev 5.3).
  yere_git {ad}         YENI (Gorev 5.4): "Anıtkabir'e git". Serbest metin alanli tek komut.

Mevcut siniflara dokunulmaz; alt siniflar yazilir:
  HaritaLLMIstemcisi(LLMIstemcisi)  genis sema + yere_git'i de kabul eden dogrulama
  HaritaKomutCozucu(KomutCozucu)    once harita hizli yolu, sonra her sey eskisi gibi
parser_node yerine harita_parser_node bunlari kullanir (harita.launch.py).
"""
import copy
import re

from . import fast_path
from .komut_cozucu import Cozum, KomutCozucu, _baglac_ayikla
from .llm_client import LLMIstemcisi, LLMSonuc, _json_ayikla, tekrar_dongusu_mu
from .prompt import SISTEM_PROMPT
from .schema import KOMUT_SEMASI, MAX_ADIM, SemaHatasi, dogrula

# ------------------------------------------------------------------ sema (Gorev 5.4)
YERE_GIT_SEMASI = {
    'type': 'object',
    'properties': {'komut': {'const': 'yere_git'}, 'ad': {'type': 'string', 'minLength': 2, 'maxLength': 60}},
    'required': ['komut', 'ad'],
    'additionalProperties': False,
}
HARITA_SEMASI = copy.deepcopy(KOMUT_SEMASI)
HARITA_SEMASI['properties']['adimlar']['items']['anyOf'].append(YERE_GIT_SEMASI)


def dogrula_genis(veri):
    """dogrula() + yere_git. Her adim tek tek: yere_git burada, digerleri dogrula()'da."""
    if not isinstance(veri, dict) or not isinstance(veri.get('adimlar'), list):
        raise SemaHatasi('"adimlar" listesi yok')
    if not 1 <= len(veri['adimlar']) <= MAX_ADIM:
        raise SemaHatasi(f'adim sayisi 1-{MAX_ADIM} olmali')
    temiz = []
    for adim in veri['adimlar']:
        if isinstance(adim, dict) and adim.get('komut') == 'yere_git':
            ad = adim.get('ad')
            if set(adim) != {'komut', 'ad'} or not isinstance(ad, str) or not 2 <= len(ad.strip()) <= 60:
                raise SemaHatasi(f'yere_git gecersiz: {adim!r}')
            temiz.append({'komut': 'yere_git', 'ad': ad.strip()})
        else:
            temiz.extend(dogrula({'adimlar': [adim]}))
    return temiz


# ------------------------------------------------------------------ few-shot prompt (hazir model)
HARITA_SISTEM_PROMPT = SISTEM_PROMPT.replace(
    '- bekle {saniye}',
    '- yere_git {ad}: adı söylenen belirli bir yere git ("Anıtkabir\'e git" -> ad: "Anıtkabir")\n'
    '- bekle {saniye}').replace(
    '"bugün hava nasıl" -> ',
    '"Anıtkabir\'e uç" -> {"adimlar":[{"komut":"yere_git","ad":"Anıtkabir"}]}\n"bugün hava nasıl" -> ')


class HaritaLLMIstemcisi(LLMIstemcisi):
    """LLMIstemcisi'nin aynisi; tek fark yere_git'i de kabul etmesi.

    Ust sinifin cevir()'i yere_git'i "bilinmeyen komut" diye reddeder ama ham cevabi saklar;
    burada ayni ham cevap genis dogrulamayla tekrar denenir. Ust sinifa dokunulmaz.
    """

    def __init__(self, *args, sema=HARITA_SEMASI, **kwargs):
        super().__init__(*args, sema=sema, **kwargs)
        if self.sistem_prompt == SISTEM_PROMPT:          # few-shot modda yere_git'i de anlat
            self.sistem_prompt = HARITA_SISTEM_PROMPT

    def cevir(self, metin):
        sonuc = super().cevir(metin)
        if sonuc.basarili or not sonuc.ham or 'yere_git' not in sonuc.ham:
            return sonuc
        try:
            adimlar = dogrula_genis(_json_ayikla(sonuc.ham))
        except (ValueError, SemaHatasi):
            return sonuc
        if tekrar_dongusu_mu(adimlar):
            return sonuc
        return LLMSonuc(adimlar=adimlar, ham=sonuc.ham, sure_ms=sonuc.sure_ms)


# ------------------------------------------------------------------ hizli yol (Gorev 5.3)
# Semadaki yer turu -> cumlede yonelme hali. "en yakın X(e) git/uç/götür/gidelim"
YER_KALIPLARI = {
    'hastane': 'hastaneye', 'eczane': 'eczaneye', 'benzinlik': "benzinliğe|akaryakıt istasyonuna",
    'polis': 'polis merkezine|karakola|polise', 'itfaiye': 'itfaiyeye|itfaiye istasyonuna',
    'okul': 'okula', 'park': 'parka', 'market': 'markete',
}
_HARITA_DESENI = re.compile(
    r'(?:bana |buraya )?en yakın (?P<yer>' + '|'.join(f'(?P<{t}>{k})' for t, k in YER_KALIPLARI.items()) +
    r')(?: kadar| doğru)? (?:git|uç|götür|gidelim|gidelim mi|gider misin|uçar mısın)')


def harita_hizli_yol(govde):
    """Normalize metin -> [{'komut': 'yakin_yere_git', 'tur': ...}] ya da None (LLM'e gider)."""
    m = _HARITA_DESENI.fullmatch(fast_path._dolgu_temizle(govde))
    if not m:
        return None
    tur = next(t for t in YER_KALIPLARI if m.group(t))
    return [{'komut': 'yakin_yere_git', 'tur': tur}]


class HaritaKomutCozucu(KomutCozucu):
    """KomutCozucu + harita hizli yolu. Acil kelime her zaman once gelir (ust sinif)."""

    def _coz(self, metin):
        if metin and self.hizli_yol and not fast_path.acil_mi(metin):
            govde, ekle = _baglac_ayikla(metin)
            adimlar = harita_hizli_yol(govde) if govde else None
            if adimlar:
                return Cozum(metin, adimlar, 'hizli_yol', ekle)
        return super()._coz(metin)
