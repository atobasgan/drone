"""Metin -> komut hatti (ROS'tan bagimsiz):

    normalize -> acil kelime -> hizli yol -> (onbellek) -> LLM

parser_node bunu kullanir; degerlendir.py ayni hatti ROS olmadan olcer.
"""
from collections import OrderedDict
from dataclasses import dataclass, field
import time

from . import fast_path
from .normalize import normalize
from .schema import bilinmiyor_mu

# Cumle bunlarla baslarsa yeni komut mevcut kuyrugun SONUNA eklenir (MIMARI 3.9)
KUYRUK_BAGLACLARI = ('sonra', 'ardından', 'daha sonra', 'ondan sonra', 'arkasından')


@dataclass
class Cozum:
    metin: str                       # normalize metin
    adimlar: list = field(default_factory=list)   # sema bicimi; bos = komut yok
    kaynak: str = ''                 # acil | hizli_yol | onbellek | llm | yok
    kuyruga_ekle: bool = False
    sure_ms: float = 0.0
    llm_ms: float = 0.0
    hata: str = ''

    @property
    def komut_var(self):
        return bool(self.adimlar)


def _baglac_ayikla(metin):
    for baglac in sorted(KUYRUK_BAGLACLARI, key=len, reverse=True):
        if metin == baglac:
            return '', True
        if metin.startswith(baglac + ' '):
            return metin[len(baglac) + 1:], True
    return metin, False


class KomutCozucu:

    def __init__(self, llm=None, hizli_yol=True, onbellek_boyutu=256):
        self.llm = llm
        self.hizli_yol = hizli_yol
        self.onbellek_boyutu = onbellek_boyutu
        self._onbellek = OrderedDict()

    def coz(self, ham_metin):
        t0 = time.perf_counter()
        metin = normalize(ham_metin)
        cozum = self._coz(metin)
        cozum.sure_ms = (time.perf_counter() - t0) * 1000
        return cozum

    def _coz(self, metin):
        if not metin:
            return Cozum(metin, kaynak='yok', hata='boş metin')

        # 1) Acil kelime: hicbir sey beklemeden DUR (baglac olsa bile)
        if fast_path.acil_mi(metin):
            return Cozum(metin, [{'komut': 'dur'}], 'acil')

        govde, ekle = _baglac_ayikla(metin)
        if not govde:
            return Cozum(metin, kaynak='yok', hata='boş metin')

        # 2) Hizli yol
        if self.hizli_yol:
            sonuc = fast_path.coz(govde)
            if sonuc is not None:
                return Cozum(metin, sonuc['adimlar'], 'hizli_yol', ekle)

        # 3) Onbellek (ayni normalize cumle tekrar gelirse)
        if govde in self._onbellek:
            self._onbellek.move_to_end(govde)
            adimlar = self._onbellek[govde]
            return Cozum(metin, list(adimlar), 'onbellek', ekle)

        # 4) LLM
        if self.llm is None:
            return Cozum(metin, kaynak='yok', kuyruga_ekle=ekle, hata='LLM yok, hızlı yol eşleşmedi')
        sonuc = self.llm.cevir(govde)
        if not sonuc.basarili:
            return Cozum(metin, kaynak='llm', kuyruga_ekle=ekle, llm_ms=sonuc.sure_ms,
                         hata=sonuc.hata)
        adimlar = [] if bilinmiyor_mu(sonuc.adimlar) else sonuc.adimlar
        self._onbellege_yaz(govde, adimlar)
        return Cozum(metin, adimlar, 'llm', ekle, llm_ms=sonuc.sure_ms,
                     hata='' if adimlar else 'anlaşılmadı (bilinmiyor)')

    def _onbellege_yaz(self, anahtar, adimlar):
        if self.onbellek_boyutu <= 0:
            return
        self._onbellek[anahtar] = tuple(adimlar)
        if len(self._onbellek) > self.onbellek_boyutu:
            self._onbellek.popitem(last=False)
