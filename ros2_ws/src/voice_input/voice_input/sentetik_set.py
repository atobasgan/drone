"""Piper TTS ile sentetik STT test seti uretir (sozluk / model karsilastirmasi icin).

    python3 -m voice_input.sentetik_set recordings/cumleler.jsonl --cikti /tmp/sentetik
    python3 -m voice_input.sentetik_set araclar/stt_sozluk/ayri_set.txt --cikti /tmp/ayri
    python3 -m voice_input.stt_karsilastir small:int8 --etiketler /tmp/ayri/etiketler.csv \\
        --sozluk yok --sozluk eski --sozluk yeni

Her cumle uc kosulda seslendirilir (kayit_al ile ayni etiketler.csv bicimi):
  temiz         : normal hiz
  hizli_gurultu : %25 hizli + ruzgar/pervane benzeri (kahverengi + pembe) gurultu, SNR 8 dB
  telefon       : %15 yavas, 300-3400 Hz bant (telefon/telsiz mikrofonu), pembe gurultu SNR 15 dB

Gercek kayitlarin yerini TUTMAZ: tek bir sentetik ses (tr_TR-dfki), temiz telaffuz.
Egilimi gosterir; karar gercek kayitlarla (kayit_al) verilir. Piper: pip install piper-tts,
ses modeli: rhasspy/piper-voices tr/tr_TR/dfki/medium (.onnx + .onnx.json).
Girdi: cumleler.jsonl ({"metin", "beklenen"}) ya da satir basina bir cumle (.txt). .txt'de
beklenen = metnin kendisinin hizli yoldan (LLM'siz) sonucu; yani komut % orada "STT, parser'in
metinden verecegi sonucu bozdu mu" sorusunu olcer (hizli yolun bilmedigi cumlede beklenen bos).
"""
import argparse
import os

import numpy as np

from .etiketler import cumleleri_oku, etiket_ekle
from .wav import HZ, wav_yaz, yeniden_ornekle

KOSULLAR = ('temiz', 'hizli_gurultu', 'telefon')
VARSAYILAN_SES = os.path.expanduser('~/piper/tr_TR-dfki-medium.onnx')


def renkli_gurultu(n, us, rng):
    """1/f^us gurultu: us=1 pembe, us=2 kahverengi (ruzgar, pervane ugultusu)."""
    f = np.fft.rfftfreq(n)
    f[0] = f[1]
    s = (rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))) / f ** (us / 2)
    g = np.fft.irfft(s, n)
    return g / np.std(g)


def snr_ile_ekle(x, gurultu, snr_db):
    return x + gurultu * np.sqrt(np.mean(x ** 2) / 10 ** (snr_db / 10))


def bant_gecir(x, alt=300, ust=3400, hz=HZ):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / hz)
    X[(f < alt) | (f > ust)] = 0
    return np.fft.irfft(X, len(x))


def kosul_uygula(seslendir, metin, kosul, rng):
    if kosul == 'temiz':
        return seslendir(metin, 1.0)
    if kosul == 'hizli_gurultu':
        x = np.concatenate([np.zeros(3200), seslendir(metin, 0.8), np.zeros(3200)])
        g = 0.6 * renkli_gurultu(len(x), 2, rng) + 0.4 * renkli_gurultu(len(x), 1, rng)
        return snr_ile_ekle(x, g, 8)
    if kosul == 'telefon':
        x = bant_gecir(seslendir(metin, 1.15))
        return snr_ile_ekle(x, renkli_gurultu(len(x), 1, rng), 15)
    raise ValueError(kosul)


def piper_seslendirici(model_yolu):
    from piper import PiperVoice, SynthesisConfig
    ses = PiperVoice.load(model_yolu)

    def seslendir(metin, hiz_olcegi):
        parcalar = list(ses.synthesize(metin, syn_config=SynthesisConfig(length_scale=hiz_olcegi)))
        ham = b''.join(p.audio_int16_bytes for p in parcalar)
        x = np.frombuffer(ham, '<i2').astype(np.float32) / 32768
        return yeniden_ornekle(x, parcalar[0].sample_rate, HZ)
    return seslendir


def cumleleri_yukle(yol):
    if yol.endswith('.jsonl'):
        return [(c['metin'], c['beklenen']['adimlar']) for c in cumleleri_oku(yol)]
    from command_parser.komut_cozucu import KomutCozucu
    cozucu = KomutCozucu(llm=None, onbellek_boyutu=0)
    with open(yol, encoding='utf-8') as f:
        metinler = [s.strip() for s in f if s.strip() and not s.startswith('#')]
    return [(m, cozucu.coz(m).adimlar) for m in metinler]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cumleler', help='cumleler.jsonl ya da satır başına bir cümle (.txt)')
    ap.add_argument('--cikti', required=True, help='WAV ve etiketler.csv bu klasöre yazılır')
    ap.add_argument('--ses', default=VARSAYILAN_SES, help='Piper .onnx ses modeli')
    ap.add_argument('--kosul', action='append', choices=KOSULLAR, help='varsayılan: üçü de')
    ap.add_argument('--tohum', type=int, default=42)
    args = ap.parse_args(argv)

    os.makedirs(args.cikti, exist_ok=True)
    csv_yolu = os.path.join(args.cikti, 'etiketler.csv')
    if os.path.exists(csv_yolu):
        os.remove(csv_yolu)
    seslendir = piper_seslendirici(args.ses)
    rng = np.random.default_rng(args.tohum)
    cumleler = cumleleri_yukle(args.cumleler)
    for i, (metin, beklenen) in enumerate(cumleler):
        for kosul in args.kosul or KOSULLAR:
            dosya = f'{i:03d}_{kosul}.wav'
            x = kosul_uygula(seslendir, metin, kosul, rng)
            wav_yaz(os.path.join(args.cikti, dosya), np.clip(x, -1, 1))
            etiket_ekle(csv_yolu, dosya, f'piper_{kosul}', metin, beklenen)
    print(f'{len(cumleler)} cümle x {len(args.kosul or KOSULLAR)} koşul -> {csv_yolu}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
