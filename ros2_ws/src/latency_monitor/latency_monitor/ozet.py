"""Gecikme CSV'sinden ortalama / p50 / p95 tablosu (Gorev 3.5). ROS gerektirmez.

    ros2 run latency_monitor ozet ~/llm_drone_gecikme/gecikme_20261104_101500.csv
    python3 -m latency_monitor.ozet gecikme.csv --tablo NOTLAR_sonuclar.md --etiket "CPU, small int8"
"""
import argparse
import datetime
import sys

from .olcum import ASAMALAR, csv_oku, en_yavas, kaynaga_gore, ozet, tablo_md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv', nargs='+', help='latency_monitor CSV dosyaları (birden fazla birleşir)')
    ap.add_argument('--tablo', default=None, help='özeti bu markdown dosyasına ekle')
    ap.add_argument('--etiket', default='', help='tablo başlığına yazılır (donanım, modeller)')
    ap.add_argument('--hepsi', action='store_true', help='reddedilen / kuyruğa eklenenleri de say')
    args = ap.parse_args(argv)

    satirlar = [s for yol in args.csv for s in csv_oku(yol)]
    if not args.hepsi:
        satirlar = [s for s in satirlar if s['sonuc'] == 'kabul']
    if not satirlar:
        print('ölçüm yok', file=sys.stderr)
        return 1

    oz = ozet(satirlar)
    baslik = f'### Gecikme — {datetime.date.today()} {args.etiket}'.rstrip()
    metin = tablo_md(oz, baslik)
    yavas = en_yavas(oz)
    if yavas:
        aciklama = dict((a[0], a[3]) for a in ASAMALAR)[yavas]
        metin += f'\nEn yavaş aşama: **{aciklama}** (ort {oz[yavas]["ort"]:.0f} ms)\n'
    metin += ('\n| kaynak | n | konuşma → komut ort ms | toplam ort ms | toplam p95 ms |\n'
              '|---|---|---|---|---|\n')
    for kaynak, k in kaynaga_gore(satirlar).items():
        metin += (f'| {kaynak} | {k["toplam_komut"]["n"]} | {k["toplam_komut"]["ort"]:.0f} '
                  f'| {k["toplam"]["ort"]:.0f} | {k["toplam"]["p95"]:.0f} |\n')
    print(metin)
    if args.tablo:
        with open(args.tablo, 'a', encoding='utf-8') as f:
            f.write(metin)
        print(f'Tabloya eklendi: {args.tablo}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
