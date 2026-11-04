"""Konusma ayirici: surekli ses akisini konusma parcalarina boler (Gorev 3.3, MIMARI 3.5).

Silero VAD her 512 ornekte (16 kHz'de 32 ms) bir konusma olasiligi verir.
KonusmaAyirici bu olasiliklardan konusmanin basini ve sonunu bulur:
  - olasilik >= esik olan cerceve konusmadir
  - konusma basladiktan sonra bitis_sessizlik_ms boyunca sessizlik -> bitti
    (bu bekleme dogrudan gecikmeye eklenir; 400 ile basla, sonra kisalt)
  - basa on_kayit_ms eklenir (ilk hece kesilmesin)
  - min_konusma_ms'den az konusma iceren parcalar atilir (klavye, tik sesi)
  - max_konusma_s asilirsa parca zorla kesilir
Olasilik fonksiyonu disaridan verilir; boylece mantik torch olmadan test edilir.
"""
from collections import deque
from dataclasses import dataclass

import numpy as np

HZ = 16000
CERCEVE = 512   # Silero VAD 16 kHz'de tam 512 ornek ister


@dataclass
class Konusma:
    ornekler: np.ndarray    # float32, 16 kHz
    bitis_ornek: int        # akisin basindan, konusmanin bittigi anlasilan ornek

    @property
    def sure_s(self):
        return len(self.ornekler) / HZ


def _cerceve_sayisi(ms):
    return int(round(ms / 1000 * HZ / CERCEVE))


class KonusmaAyirici:

    def __init__(self, olasilik, esik=0.5, bitis_sessizlik_ms=400, on_kayit_ms=200,
                 min_konusma_ms=250, max_konusma_s=10.0):
        self.olasilik = olasilik
        self.esik = esik
        self.bitis_cerceve = max(1, _cerceve_sayisi(bitis_sessizlik_ms))
        self.min_cerceve = max(1, _cerceve_sayisi(min_konusma_ms))
        self.max_cerceve = max(1, _cerceve_sayisi(max_konusma_s * 1000))
        self._on = deque(maxlen=_cerceve_sayisi(on_kayit_ms))
        self._tampon = np.zeros(0, np.float32)
        self._ornek = 0
        self._sifirla_parca()

    def _sifirla_parca(self):
        self.konusuyor = False
        self._parca = []
        self._konusma = 0      # parcadaki esik ustu cerceve sayisi
        self._sessiz = 0       # sondaki ardisik sessiz cerceve sayisi

    def sifirla(self):
        self._on.clear()
        self._tampon = np.zeros(0, np.float32)
        self._sifirla_parca()
        sifirla = getattr(self.olasilik, 'sifirla', None)
        if sifirla:
            sifirla()

    def besle(self, ornekler):
        """Herhangi uzunlukta float32 parca alir; biten konusmalarin listesini dondurur."""
        self._tampon = np.concatenate([self._tampon, np.asarray(ornekler, np.float32)])
        biten = []
        while len(self._tampon) >= CERCEVE:
            c, self._tampon = self._tampon[:CERCEVE], self._tampon[CERCEVE:]
            self._ornek += CERCEVE
            k = self._cerceve(c)
            if k is not None:
                biten.append(k)
        return biten

    def bosalt(self):
        """Akis bitti (dosya sonu): devam eden konusmayi bitirir."""
        return self._bitir() if self.konusuyor else None

    def _cerceve(self, c):
        konusma = self.olasilik(c) >= self.esik
        if not self.konusuyor:
            if konusma:
                self.konusuyor = True
                self._parca = list(self._on) + [c]
                self._konusma = 1
            else:
                self._on.append(c)
            return None

        self._parca.append(c)
        if konusma:
            self._konusma += 1
            self._sessiz = 0
        else:
            self._sessiz += 1
        if self._sessiz >= self.bitis_cerceve or len(self._parca) >= self.max_cerceve:
            return self._bitir()
        return None

    def _bitir(self):
        parca, konusma, sessiz = self._parca, self._konusma, self._sessiz
        self._sifirla_parca()
        self._on.clear()
        if konusma < self.min_cerceve:
            return None
        # Sondaki sessizligin ~100 ms'si kalsin, gerisi STT'ye gitmesin.
        kes = max(0, sessiz - 3)
        if kes:
            parca = parca[:-kes]
        return Konusma(np.concatenate(parca), self._ornek)


class SileroVAD:
    """Silero VAD (pip: silero-vad). Cagrilinca 512 ornekli cercevenin olasiligini verir."""

    def __init__(self, thread=1):
        import torch
        from silero_vad import load_silero_vad
        torch.set_num_threads(thread)
        self._torch = torch
        self.model = load_silero_vad()

    def __call__(self, cerceve):
        with self._torch.no_grad():
            return float(self.model(self._torch.from_numpy(cerceve), HZ).item())

    def sifirla(self):
        self.model.reset_states()
