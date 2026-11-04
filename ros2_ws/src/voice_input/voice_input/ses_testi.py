"""Uctan uca sesli test (Gorev 3.4): kayitli WAV'lari sirayla calisan sisteme verir.

Her dosya icin: /voice/dosya'ya yol yayinlanir -> stt_node (dosya modu) ->
/voice/stt -> command_parser -> /drone/command. Uretilen komut beklenen JSON ile
karsilastirilir. Gecikmeler ayni anda latency_monitor'un CSV'sine yazilir (3.5).

    ros2 launch drone_bringup all.launch.py stt_mod:=ikisi     # ya da ses_test.launch.py
    ros2 run voice_input ses_testi --etiket "small int8 + qwen3-1.7b" --tablo NOTLAR_sonuclar.md

Yurutucu acikken drone komutlari gercekten ucar; yalnizca dogruluk icin
ses_test.launch.py (stt + parser + latency_monitor, yurutucusuz) yeterli.
"""
import argparse
import csv
import datetime
import os
import statistics
import sys
import threading
import time

from command_parser.normalize import normalize
from command_parser.schema import msg_alanlarindan
from drone_interfaces.msg import CommandList, Feedback, VoiceText
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String

from .etiketler import etiketleri_oku, karsilastir, varsayilan_klasor, yuzdelik

ALANLAR = ('komut', 'metre', 'derece', 'yon', 'enlem', 'boylam', 'tur', 'saniye', 'mps')


class SesTesti(Node):

    def __init__(self):
        super().__init__('ses_testi')
        self.pub = self.create_publisher(String, '/voice/dosya', 10)
        self.create_subscription(VoiceText, '/voice/stt', self._stt_cb, 10)
        self.create_subscription(CommandList, '/drone/command', self._komut_cb, 10)
        self.create_subscription(Feedback, '/drone/feedback', self._fb_cb, 10)
        self._kilit = threading.Lock()
        self._olay = threading.Event()
        self._bekleyen = None

    def gonder(self, yol, zaman_asimi):
        """Dosyayi gonderir; (duyulan metin, uretilen adimlar, sure_s) dondurur."""
        with self._kilit:
            self._bekleyen, self._stt, self._adimlar = yol, None, None
            self._olay.clear()
        t0 = time.perf_counter()
        self.pub.publish(String(data=yol))
        bitti = self._olay.wait(zaman_asimi)
        with self._kilit:
            self._bekleyen = None
            metin = self._stt.metin if self._stt is not None else None
            return metin, (self._adimlar or []), (time.perf_counter() - t0), bitti

    def _bitir(self, adimlar):
        if self._adimlar is None:
            self._adimlar = adimlar
            self._olay.set()

    def _stt_cb(self, m):
        with self._kilit:
            if self._bekleyen and m.dosya == self._bekleyen:
                self._stt = m
                if not m.metin.strip():      # parser bos metni yok sayar
                    self._bitir([])

    def _komut_cb(self, m):
        with self._kilit:
            if self._bekleyen and m.ses_kaynagi == 'dosya':
                self._bitir([msg_alanlarindan({a: getattr(adim, a) for a in ALANLAR})
                             for adim in m.adimlar])

    def _fb_cb(self, m):
        # parser'in "anlamadım" reddi = komut uretilmedi
        with self._kilit:
            if self._bekleyen and self._stt is not None and m.durum == 'reddedildi' \
                    and m.mesaj.startswith('anlamadım'):
                self._bitir([])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--etiketler', default=os.path.join(varsayilan_klasor(), 'etiketler.csv'))
    ap.add_argument('--zaman-asimi', type=float, default=15.0, help='dosya başına en fazla saniye')
    ap.add_argument('--ara', type=float, default=0.5, help='dosyalar arası bekleme (s)')
    ap.add_argument('--cikti', default=None, help='dosya başına sonuçları bu CSV\'ye yaz')
    ap.add_argument('--tablo', default=None, help='özeti bu markdown dosyasına ekle')
    ap.add_argument('--etiket', default='', help='tabloda görünecek ad (STT + LLM modeli)')
    args = ap.parse_args(argv)

    satirlar = etiketleri_oku(args.etiketler)
    if not satirlar:
        print(f'kayıt yok: {args.etiketler}', file=sys.stderr)
        return 1

    rclpy.init()
    node = SesTesti()
    yurutucu = SingleThreadedExecutor()
    yurutucu.add_node(node)
    threading.Thread(target=yurutucu.spin, daemon=True).start()
    try:
        for _ in range(50):
            if node.count_subscribers('/voice/dosya'):
                break
            time.sleep(0.1)
        else:
            print('/voice/dosya dinleyen yok: stt_node dosya modunda çalışıyor mu? '
                  '(stt_mod:=dosya ya da ikisi)', file=sys.stderr)
            return 1

        tam = komut = cumle = negatif = yanlis_kabul = zaman_asimi = 0
        sureler, kayitlar = [], []
        for i, s in enumerate(satirlar, 1):
            duyulan, adimlar, sure, bitti = node.gonder(s['yol'], args.zaman_asimi)
            t, k, neg = karsilastir(adimlar, s['beklenen'])
            c = duyulan is not None and normalize(duyulan) == normalize(s['metin'])
            tam += t
            komut += k
            cumle += c
            negatif += neg
            yanlis_kabul += neg and not t
            zaman_asimi += not bitti
            if bitti:
                sureler.append(sure * 1000)
            kayitlar.append({'dosya': s['dosya'], 'okunan': s['metin'], 'duyulan': duyulan or '',
                             'uretilen': adimlar, 'beklenen': s['beklenen'],
                             'tam_dogru': int(t), 'sure_ms': round(sure * 1000)})
            durum = 'OK  ' if t else ('ZAMAN' if not bitti else 'HATA')
            print(f'[{i:3}/{len(satirlar)}] {durum} {sure * 1000:6.0f} ms  "{s["metin"]}" -> "{duyulan}"')
            if not t:
                print(f'          beklenen {s["beklenen"]}\n          üretilen {adimlar}')
            time.sleep(args.ara)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    n = len(satirlar)
    ozet = {
        'n': n, 'cumle': cumle / n * 100, 'tam': tam / n * 100, 'komut': komut / n * 100,
        'yanlis_kabul': yanlis_kabul / negatif * 100 if negatif else 0.0,
        'ort': statistics.mean(sureler) if sureler else 0.0, 'p95': yuzdelik(sureler, 95),
    }
    print(f'\n=== uçtan uca ({n} kayıt) ===\n'
          f'STT cümle doğru : %{ozet["cumle"]:.1f}\n'
          f'tam eşleşme     : %{ozet["tam"]:.1f}\n'
          f'komut türü      : %{ozet["komut"]:.1f}\n'
          f'yanlış kabul    : %{ozet["yanlis_kabul"]:.1f}\n'
          f'süre (dosya gönder -> komut): ort {ozet["ort"]:.0f} ms, p95 {ozet["p95"]:.0f} ms\n'
          f'zaman aşımı     : {zaman_asimi}')

    if args.tablo:
        with open(args.tablo, 'a', encoding='utf-8') as f:
            f.write('\n| tarih | uçtan uca (ses) | n | STT cümle % | tam eşleşme % | komut % '
                    '| yanlış kabul % | ort ms | p95 ms |\n|---|---|---|---|---|---|---|---|---|\n'
                    f'| {datetime.date.today()} | {args.etiket} | {n} | {ozet["cumle"]:.1f} '
                    f'| {ozet["tam"]:.1f} | {ozet["komut"]:.1f} | {ozet["yanlis_kabul"]:.1f} '
                    f'| {ozet["ort"]:.0f} | {ozet["p95"]:.0f} |\n')
        print(f'Tabloya eklendi: {args.tablo}')
    if args.cikti:
        with open(args.cikti, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(kayitlar[0]))
            w.writeheader()
            w.writerows(kayitlar)
    return 0


if __name__ == '__main__':
    sys.exit(main())
