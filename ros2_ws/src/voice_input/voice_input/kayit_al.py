"""Test kayitlarini olusturur (Gorev 3.1): cumleyi gosterir, sen okursun, WAV + etiket yazilir.

    python3 -m voice_input.kayit_al --konusmaci atakan
    ros2 run voice_input kayit_al --konusmaci yigit

Her cumle icin: Enter -> kayit baslar, cumleyi oku, Enter -> durur.
Sonra: Enter = kaydet, t = tekrar kaydet, d = dinle, a = atla, q = cik.
Kayitlar <klasor>/<konusmaci>_<sira>.wav (16 kHz mono), etiketler <klasor>/etiketler.csv.
Yarida birakirsan ayni komutla kaldigin yerden devam eder.
ROS gerektirmez; mikrofonlu herhangi bir bilgisayarda calisir (pip: sounddevice numpy).
"""
import argparse
import os
import sys

import numpy as np

from .etiketler import cumleleri_oku, etiket_ekle, etiketleri_oku, varsayilan_klasor
from .wav import HZ, wav_yaz


def kaydet(cihaz):
    import sounddevice as sd
    parcalar = []
    with sd.InputStream(samplerate=HZ, channels=1, dtype='float32', device=cihaz,
                        callback=lambda v, *_: parcalar.append(v[:, 0].copy())):
        input('  ● kayıt... bitince Enter ')
    return np.concatenate(parcalar) if parcalar else np.zeros(0, np.float32)


def seviye_uyarisi(x):
    if len(x) < HZ * 0.3:
        return 'çok kısa'
    tepe = float(np.abs(x).max())
    if tepe < 0.02:
        return f'çok sessiz (tepe {tepe:.3f}); mikrofona yaklaş'
    if tepe > 0.99:
        return 'kırpılmış (çok yüksek); mikrofondan uzaklaş'
    return ''


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--konusmaci', required=True, help='dosya adlarında kullanılır (ör. atakan)')
    ap.add_argument('--klasor', default=varsayilan_klasor())
    ap.add_argument('--cumleler', default=None, help='varsayılan: <klasor>/cumleler.jsonl')
    ap.add_argument('--cihaz', default=None, help='mikrofon numarası ya da adı (python3 -m sounddevice)')
    args = ap.parse_args(argv)

    konusmaci = args.konusmaci.strip().lower().replace(' ', '_')
    cumleler = cumleleri_oku(args.cumleler or os.path.join(args.klasor, 'cumleler.jsonl'))
    csv_yolu = os.path.join(args.klasor, 'etiketler.csv')
    yapilan = set()
    if os.path.exists(csv_yolu):
        yapilan = {(s['konusmaci'], s['metin']) for s in etiketleri_oku(csv_yolu)}
    cihaz = int(args.cihaz) if args.cihaz and args.cihaz.isdigit() else args.cihaz

    kalan = [(i, c) for i, c in enumerate(cumleler, 1) if (konusmaci, c['metin']) not in yapilan]
    print(f'{len(cumleler)} cümle, {len(cumleler) - len(kalan)} tanesi zaten kayıtlı. '
          f'Doğal konuş; cümleyi birebir okumak zorunda değilsin ama anlamını değiştirme.')
    for sira, (i, cumle) in enumerate(kalan, 1):
        print(f'\n[{sira}/{len(kalan)}]  "{cumle["metin"]}"')
        if input('  Enter = başla, q = çık: ').strip().lower() == 'q':
            break
        x = kaydet(cihaz)
        while True:
            uyari = seviye_uyarisi(x)
            print(f'  {len(x) / HZ:.1f} sn' + (f'  !! {uyari}' if uyari else ''))
            secim = input('  Enter = kaydet, t = tekrar, d = dinle, a = atla, q = çık: ').strip().lower()
            if secim == 'd':
                import sounddevice as sd
                sd.play(x, HZ)
                sd.wait()
            elif secim == 't':
                x = kaydet(cihaz)
            elif secim in ('a', 'q', ''):
                break
        if secim == 'q':
            break
        if secim == 'a':
            continue
        dosya = f'{konusmaci}_{i:03d}.wav'
        wav_yaz(os.path.join(args.klasor, dosya), x)
        etiket_ekle(csv_yolu, dosya, konusmaci, cumle['metin'], cumle['beklenen']['adimlar'])
        print(f'  -> {dosya}')
    print(f'\nEtiketler: {csv_yolu}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
