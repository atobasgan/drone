"""STT motoru: faster-whisper sarmalayici (Gorev 3.2 / 3.3, MIMARI 3.6).

Ayarlar: language='tr' sabit (dil algilama atlanir), beam_size=1, sicaklik 0
(geri dusme denemesi yok), initial_prompt = drone sozlugu (Whisper bu kelimelere
yatkinlasir). Sessizlik / Whisper'in bilinen uydurmalari bos metin dondurur.
"""
from dataclasses import dataclass
import difflib
import time

import numpy as np

DRONE_SOZLUGU = (
    'Drone komutları: kalk, kalkış yap, in, iniş yap, yüksel, alçal, metre, '
    'metreye çık, irtifa, ileri, geri, sağa, sola, kuzeye, güneye, doğuya, batıya, '
    'git, dön, derece, bekle, saniye, hız, eve dön, dur, acil, en yakın hastane, '
    'eczane, benzinlik.'
)

# Whisper sessizlikte / gurultude bunlari uydurur (Turkce altyazi verisinden).
HALUSINASYONLAR = ('altyazı', 'abone ol', 'izlediğiniz için', 'www.', 'm.k.')


def halusinasyon_mu(metin):
    m = metin.lower()
    return any(h in m for h in HALUSINASYONLAR)


def aday_ayristir(tanim):
    """'small:int8', 'large-v3-turbo:float16@cuda', 'kisi/model-ct2' -> (model, hesaplama, cihaz)."""
    tanim, _, cihaz = tanim.partition('@')
    model, ayrac, hesaplama = tanim.rpartition(':')
    if not ayrac:
        model, hesaplama = tanim, 'int8'
    return model, hesaplama, cihaz or 'auto'


@dataclass
class STTSonucu:
    metin: str
    sure_ms: float
    atilan: str = ''     # sessizlik / uydurma diye atilan parcalar (log icin)


class FasterWhisperSTT:

    def __init__(self, model='small', cihaz='auto', hesaplama='int8', beam_size=1,
                 ilk_prompt=DRONE_SOZLUGU, dil='tr', thread=0, sessizlik_esigi=0.6):
        from faster_whisper import WhisperModel
        self.ad = f'{model}:{hesaplama}@{cihaz}'
        self.model = WhisperModel(model, device=cihaz, compute_type=hesaplama, cpu_threads=thread)
        self.beam_size = beam_size
        self.ilk_prompt = ilk_prompt or None
        self.dil = dil
        self.sessizlik_esigi = sessizlik_esigi

    def cevir(self, ornekler):
        """float32 16 kHz ses -> metin."""
        t0 = time.perf_counter()
        segmentler, _ = self.model.transcribe(
            np.asarray(ornekler, np.float32), language=self.dil, beam_size=self.beam_size,
            initial_prompt=self.ilk_prompt, temperature=0.0, vad_filter=False,
            condition_on_previous_text=False, without_timestamps=True)
        metinler, atilan = [], []
        for s in segmentler:     # uretec: cozme burada calisir
            if s.no_speech_prob > self.sessizlik_esigi and s.avg_logprob < -1.0:
                atilan.append(s.text.strip())
            else:
                metinler.append(s.text.strip())
        metin = ' '.join(m for m in metinler if m)
        if halusinasyon_mu(metin):
            atilan.append(metin)
            metin = ''
        return STTSonucu(metin, (time.perf_counter() - t0) * 1000, ' | '.join(atilan))

    def isit(self):
        """Ilk cagri yavastir (bellek ayirma, cekirdek derleme); acilista bir kez calistir."""
        return self.cevir(np.zeros(16000, np.float32)).sure_ms


def kelime_farklari(beklenen, duyulan):
    """Normalize iki cumle arasindaki kelime farklari: [(beklenen, duyulan), ...].

    Eksik kelime ('yüksel', ''), fazla kelime ('', 've'), yanlis ('alçal', 'açal').
    """
    b, d = beklenen.split(), duyulan.split()
    farklar = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=b, b=d, autojunk=False).get_opcodes():
        if op != 'equal':
            farklar.append((' '.join(b[i1:i2]), ' '.join(d[j1:j2])))
    return farklar
