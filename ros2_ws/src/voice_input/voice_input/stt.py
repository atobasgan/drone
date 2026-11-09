"""STT motoru: faster-whisper sarmalayici (Gorev 3.2 / 3.3, MIMARI 3.6).

Ayarlar: language='tr' sabit (dil algilama atlanir), beam_size=1, sicaklik 0
(geri dusme denemesi yok), initial_prompt = drone sozlugu (stt_sozlugu.py; Whisper
bu kelimelere ve emir kipine yatkinlasir). Sessizlik / Whisper'in bilinen
uydurmalari bos metin dondurur.
"""
from dataclasses import dataclass
import difflib
import re
import time

import numpy as np

from .stt_sozlugu import DRONE_SOZLUGU, siniri_kontrol_et  # noqa: F401 (DRONE_SOZLUGU disari)

# Whisper sessizlikte / gurultude bunlari uydurur (Turkce altyazi verisinden).
HALUSINASYONLAR = ('altyazı', 'abone ol', 'izlediğiniz için', 'www.', 'm.k.')


# Whisper'in kendi esigi: metin zlib ile bu orandan fazla sikisiyorsa tekrar dongusudur
# ("5 metre, 5 metre, 5 metre, ..."). sicaklik 0 sabit oldugu icin Whisper yeniden denemez.
TEKRAR_ORANI = 2.4
# Sozlukten kopya icin no_speech_prob esigi. Olcum (DRONE_SOZLUGU.txt Bolum 7): gurultuden
# sozlukten kopyalanan cumlelerde 0.58-0.88; 501 konusma segmentinde 0.5'i asan 2 tane (kopya
# degildi). Pay ince: bu filtre VAD'dan sonra ikinci savunma hattidir.
KOPYA_SESSIZLIK_ESIGI = 0.5
# Durdurma iceren metin hicbir filtreyle atilmaz: yanlislikla durmak her zaman guvenli.
DURDURMA = frozenset({'dur', 'durdur', 'stop', 'acil', 'iptal', 'vazgeç', 'fren'})


def halusinasyon_mu(metin):
    m = metin.lower()
    return any(h in m for h in HALUSINASYONLAR)


def _sade(metin):
    # Turkce kucuk harf: 'İ'.lower() Python'da 'i' + birlesik nokta verir.
    metin = metin.replace('İ', 'i').replace('I', 'ı').lower()
    return ' '.join(re.sub(r'[^\w\s]', ' ', metin).split())


def durdurma_mi(metin):
    return not DURDURMA.isdisjoint(_sade(metin).split())


def sozlukten_kopya_mi(metin, sozluk):
    """Ses yokken Whisper initial_prompt'tan kelime kopyalar ("Yüksel, irtifa kaybet, irtifa
    kaybet."); sira karisik olabilir. Butun kelimeleri sozlukte geciyorsa kopya sayilir."""
    kelimeler = set(_sade(metin).split())
    return bool(kelimeler and sozluk) and kelimeler <= set(_sade(sozluk).split())


def aday_ayristir(tanim):
    """'small:int8', 'large-v3-turbo:float16@cuda', 'kisi/model-ct2' -> (model, hesaplama, cihaz)."""
    tanim, _, cihaz = tanim.partition('@')
    model, ayrac, hesaplama = tanim.rpartition(':')
    if not ayrac:
        model, hesaplama = tanim, 'int8'
    return model, hesaplama, cihaz or 'auto'


def segmentleri_suz(segmentler, sozluk=None, sessizlik_esigi=0.6):
    """Whisper segmentleri -> (metin, atilanlar). Uydurma ve tekrar dongulerini ayiklar.

    Durdurma iceren metin atilmaz (DURDURMA): suphede drone durmali, hareket etmemeli.
    """
    metinler, atilan = [], []
    for s in segmentler:
        metin = s.text.strip()
        if s.compression_ratio > TEKRAR_ORANI:
            atilan.append(f'tekrar: {metin[:40]}')
            if durdurma_mi(metin):          # "Dur. Dur. Dur. ..." -> bir kez "Dur."
                metinler.append(re.split(r'(?<=[.!?,])\s', metin)[0])
        elif s.no_speech_prob > sessizlik_esigi and s.avg_logprob < -1.0:
            atilan.append(metin)
        elif (s.no_speech_prob > KOPYA_SESSIZLIK_ESIGI and not durdurma_mi(metin)
              and sozlukten_kopya_mi(metin, sozluk)):
            # Ses yokken sozlukten kopyalanan cumle modele "kolay" gelir (logprob yuksek);
            # onu yalniz no_speech_prob ele verir.
            atilan.append(f'sözlükten kopya: {metin}')
        else:
            metinler.append(metin)
    metin = ' '.join(m for m in metinler if m)
    if halusinasyon_mu(metin):
        atilan.append(metin)
        metin = ''
    return metin, atilan


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
        self.prompt_token = siniri_kontrol_et(self.model.hf_tokenizer, ilk_prompt or '')
        self.dil = dil
        self.sessizlik_esigi = sessizlik_esigi

    def cevir(self, ornekler):
        """float32 16 kHz ses -> metin."""
        t0 = time.perf_counter()
        segmentler, _ = self.model.transcribe(
            np.asarray(ornekler, np.float32), language=self.dil, beam_size=self.beam_size,
            initial_prompt=self.ilk_prompt, temperature=0.0, vad_filter=False,
            condition_on_previous_text=False, without_timestamps=True)
        # segmentler bir uretec: cozme suz() icinde, ilk segment istenince calisir
        metin, atilan = segmentleri_suz(segmentler, self.ilk_prompt, self.sessizlik_esigi)
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
