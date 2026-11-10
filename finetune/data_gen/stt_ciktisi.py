"""Gorev 4.3: gercek STT ciktilari -> ek egitim verisi (yalniz train cumlelerinden).

    python3 -m finetune.data_gen.stt_ciktisi --adet 400 --cikti finetune/data/stt_ciktilari.jsonl
    python3 -m finetune.data_gen.uret --ek-veri finetune/data/stt_ciktilari.jsonl

Insan kaydi yokken: train cumlesi -> Piper TTS (3 kosul: temiz / gurultu / telefon,
voice_input.sentetik_set) -> faster-whisper (Faz 3 ayarlari + drone sozlugu) -> metin.
Etiket cumlenin kendi etiketidir. Whisper sayiyi yanlis duyduysa ornek uret.py'nin
kontrolunde atilir (yanlis sayi ogretmeyiz). Insan kayitlari gelince ayni bicimde
(metin = STT ciktisi, beklenen = okunan cumlenin etiketi) bu dosyaya eklenir;
TEST icin ayrilan konusmacilarin kayitlari EKLENMEZ.
"""
import argparse
import json
import os
import random
import sys

from ..ortak import KOK, VERI, jsonl_oku, jsonl_yaz

sys.path.insert(0, os.path.join(KOK, 'ros2_ws', 'src', 'voice_input'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--adet', type=int, default=400)
    ap.add_argument('--cikti', default=os.path.join(VERI, 'stt_ciktilari.jsonl'))
    ap.add_argument('--ses', default=os.path.expanduser('~/piper/tr_TR-dfki-medium.onnx'))
    ap.add_argument('--stt-model', default='small')
    ap.add_argument('--tohum', type=int, default=3)
    args = ap.parse_args(argv)

    from voice_input.sentetik_set import KOSULLAR, kosul_uygula, piper_seslendirici
    from voice_input.stt import FasterWhisperSTT
    import numpy as np

    rng = random.Random(args.tohum)
    temiz = [s for s in jsonl_oku(os.path.join(VERI, 'train.jsonl')) if not s['meta']['gurultu']]
    secilen = rng.sample(temiz, min(args.adet, len(temiz)))
    seslendir = piper_seslendirici(args.ses)
    stt = FasterWhisperSTT(args.stt_model)
    nrng = np.random.default_rng(args.tohum)
    satirlar = []
    for i, s in enumerate(secilen):
        kosul = KOSULLAR[i % len(KOSULLAR)]
        ses = np.clip(kosul_uygula(seslendir, s['meta']['ham'], kosul, nrng), -1, 1)
        duyulan = stt.cevir(ses).metin
        if duyulan:
            satirlar.append({'metin': duyulan, 'beklenen': json.loads(s['messages'][2]['content']),
                             'okunan': s['meta']['ham'], 'kosul': kosul})
        if i % 50 == 0:
            print(f'{i}/{len(secilen)} {s["meta"]["ham"]!r} -> {duyulan!r}', flush=True)
    jsonl_yaz(args.cikti, satirlar)
    print(f'{len(satirlar)} STT çıktısı -> {args.cikti}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
