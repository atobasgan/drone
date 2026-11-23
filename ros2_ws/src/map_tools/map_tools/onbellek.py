"""Gorev 5.2 "sonuclari onbellege al": herhangi bir saglayiciyi saran onbellek.

Ayni tur/ad ve ~50 m icindeki ayni nokta icin servis tekrar cagrilmaz (kota ve gecikme).
Mesafe her seferinde guncel konumdan yeniden hesaplanir. "Bulunamadi" da onbellege girer,
HATA (zaman asimi, internet yok) girmez: bir sonraki istek tekrar dener.
"""
import math
import time

from mission_executor.geo import haversine_m

from .yer import Yer


class OnbellekliSaglayici:

    def __init__(self, ic, sure_s=600.0, izgara_m=50.0, saat=time.monotonic):
        self.ic, self.sure_s, self.izgara_m, self.saat = ic, sure_s, izgara_m, saat
        self.ad = ic.ad
        self._kayitlar = {}

    def _hucre(self, enlem, boylam):
        kuzey = enlem * 111320.0
        dogu = boylam * 111320.0 * math.cos(math.radians(enlem))
        return round(kuzey / self.izgara_m), round(dogu / self.izgara_m)

    def _sor(self, anahtar, enlem, boylam, cagri):
        anahtar = anahtar + self._hucre(enlem, boylam)
        kayit = self._kayitlar.get(anahtar)
        if kayit is None or self.saat() - kayit[0] > self.sure_s:
            kayit = (self.saat(), cagri())                   # HaritaHatasi burada yukari gecer
            self._kayitlar[anahtar] = kayit
        yer = kayit[1]
        if yer is None:
            return None
        return Yer(yer.ad, yer.enlem, yer.boylam, haversine_m(enlem, boylam, yer.enlem, yer.boylam), yer.kaynak)

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        return self._sor(('en_yakin', tur, yaricap_m), enlem, boylam,
                         lambda: self.ic.en_yakin(tur, enlem, boylam, yaricap_m))

    def ara(self, ad, enlem, boylam, yaricap_m):
        return self._sor(('ara', ad.casefold(), yaricap_m), enlem, boylam,
                         lambda: self.ic.ara(ad, enlem, boylam, yaricap_m))
