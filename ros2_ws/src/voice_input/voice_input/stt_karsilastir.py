"""STT adaylarini kayitli test setiyle karsilastirir (Gorev 3.2). ROS gerektirmez.

    python3 -m voice_input.stt_karsilastir small:int8 medium:int8
    python3 -m voice_input.stt_karsilastir large-v3-turbo:float16@cuda --tablo NOTLAR_sonuclar.md
    python3 -m voice_input.stt_karsilastir small:int8 --llm http://127.0.0.1:8080   # + LLM
    python3 -m voice_input.stt_karsilastir small:int8 --sozluk eski --sozluk yeni   # sozluk etkisi
    python3 -m voice_input.stt_karsilastir small:int8 --sozluk benim_sozlugum.txt

Aday bicimi: <model>[:<hesaplama>][@<cihaz>]. Model bir faster-whisper boyutu
(tiny, base, small, medium, large-v3-turbo) ya da Hugging Face'teki bir
CTranslate2 deposu olabilir (Turkce fine-tune'lu surumler).

Her aday icin:
  cumle %  : normalize(STT) == normalize(okunan cumle)
  komut %  : ses -> STT -> normalize -> hizli yol (-> LLM) -> beklenen JSON (uctan uca, ROS'suz)
  STT ms   : dosya basina ortalama / p95, RTF = STT suresi / ses suresi
Sonda en sik yanlis duyulan kelimeler (Faz 4 veri uretiminde STT gurultusu icin).
"""
import argparse
from collections import Counter
import csv
import datetime
import os
import statistics
import sys

from command_parser.komut_cozucu import KomutCozucu
from command_parser.normalize import normalize

from .etiketler import etiketleri_oku, karsilastir, varsayilan_klasor, yuzdelik
from .stt import FasterWhisperSTT, aday_ayristir, kelime_farklari
from .stt_sozlugu import sozluk_sec
from .wav import HZ, wav_oku


def adayi_olc(stt, satirlar, cozucu, ayrintili=False):
    cumle = tam = komut = 0
    sureler, rtf = [], []
    farklar = Counter()
    kayitlar = []
    for s in satirlar:
        x = wav_oku(s['yol'])
        sonuc = stt.cevir(x)
        sureler.append(sonuc.sure_ms)
        rtf.append(sonuc.sure_ms / 1000 / max(len(x) / HZ, 1e-3))
        beklenen_n, duyulan_n = normalize(s['metin']), normalize(sonuc.metin)
        cumle_dogru = beklenen_n == duyulan_n
        cumle += cumle_dogru
        farklar.update(kelime_farklari(beklenen_n, duyulan_n))
        t, k, _ = karsilastir(cozucu.coz(sonuc.metin).adimlar, s['beklenen'])
        tam += t
        komut += k
        kayitlar.append({'aday': stt.ad, 'dosya': s['dosya'], 'okunan': s['metin'],
                         'duyulan': sonuc.metin, 'cumle_dogru': int(cumle_dogru),
                         'komut_dogru': int(t), 'stt_ms': round(sonuc.sure_ms, 1)})
        if ayrintili:
            print(f'  {"OK " if cumle_dogru else "--"} {"OK " if t else "HATA"} {sonuc.sure_ms:6.0f} ms  '
                  f'"{s["metin"]}" -> "{sonuc.metin}"')
    n = len(satirlar)
    return {
        'aday': stt.ad, 'n': n,
        'cumle': cumle / n * 100, 'tam': tam / n * 100, 'komut': komut / n * 100,
        'ort_ms': statistics.mean(sureler), 'p95_ms': yuzdelik(sureler, 95),
        'rtf': statistics.mean(rtf), 'farklar': farklar, 'kayitlar': kayitlar,
    }


BASLIK = ('| tarih | STT adayı | n | cümle doğru % | komut tam % | komut türü % '
          '| STT ort ms | STT p95 ms | RTF |\n|---|---|---|---|---|---|---|---|---|\n')


def satir(s, etiket=''):
    return (f'| {datetime.date.today()} | {s["aday"]}{etiket} | {s["n"]} | {s["cumle"]:.1f} '
            f'| {s["tam"]:.1f} | {s["komut"]:.1f} | {s["ort_ms"]:.0f} | {s["p95_ms"]:.0f} '
            f'| {s["rtf"]:.2f} |\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('adaylar', nargs='+', help='ör. small:int8 large-v3-turbo:float16@cuda')
    ap.add_argument('--etiketler', default=os.path.join(varsayilan_klasor(), 'etiketler.csv'))
    ap.add_argument('--llm', default=None, help='llama-server adresi; yoksa yalnızca hızlı yol')
    ap.add_argument('--sozluk', action='append', default=None,
                    help='initial_prompt: yeni (varsayılan) | eski | yok | dosya.txt; '
                         'birden çok kez verilirse her aday her sözlükle ölçülür')
    ap.add_argument('--sozluksuz', action='store_true', help='--sozluk yok ile aynı')
    ap.add_argument('--beam', type=int, default=1)
    ap.add_argument('--thread', type=int, default=0, help='CPU thread sayısı (0 = varsayılan)')
    ap.add_argument('--hatalar', type=int, default=15, help='en sık yanlış duyulan kaç kelime')
    ap.add_argument('--cikti', default=None, help='dosya başına sonuçları bu CSV\'ye yaz (Faz 4 verisi)')
    ap.add_argument('--tablo', default=None, help='sonucu bu markdown dosyasına ekle')
    ap.add_argument('--etiket', default='', help='tabloda adayın yanına yazılır (ör. "CPU 4c")')
    ap.add_argument('-v', '--ayrintili', action='store_true')
    args = ap.parse_args(argv)

    satirlar = etiketleri_oku(args.etiketler)
    if not satirlar:
        print(f'kayıt yok: {args.etiketler} (önce: kayit_al)', file=sys.stderr)
        return 1
    print(f'{len(satirlar)} kayıt: {args.etiketler}')

    llm = None
    if args.llm:
        from command_parser.llm_client import LLMIstemcisi
        llm = LLMIstemcisi(url=args.llm)
        if not llm.saglikli():
            print(f'llama-server\'a ulaşılamadı: {args.llm}', file=sys.stderr)
            return 1
        llm.isit()
    cozucu = KomutCozucu(llm=llm, onbellek_boyutu=0)

    sozlukler = ['yok'] if args.sozluksuz else (args.sozluk or ['yeni'])
    coklu = len(sozlukler) > 1
    sonuclar = []
    for tanim in args.adaylar:
        model, hesaplama, cihaz = aday_ayristir(tanim)
        for sozluk in sozlukler:
            print(f'\n=== {tanim}, sözlük: {sozluk}: yükleniyor ===')
            stt = FasterWhisperSTT(model, cihaz=cihaz, hesaplama=hesaplama, beam_size=args.beam,
                                   ilk_prompt=sozluk_sec(sozluk), thread=args.thread)
            print(f'initial_prompt: {stt.prompt_token} token')
            stt.isit()
            s = adayi_olc(stt, satirlar, cozucu, args.ayrintili)
            if coklu or sozluk != 'yeni':
                s['aday'] += f' [sözlük: {sozluk}]'
            sonuclar.append(s)
            del stt

    etiket = ' ' + args.etiket if args.etiket else ''
    print('\n' + BASLIK + ''.join(satir(s, etiket) for s in sonuclar), end='')
    print(f'(komut: {"hızlı yol + LLM" if llm else "yalnızca hızlı yol; LLM için --llm"})')
    for s in sonuclar:
        print(f'\nEn sık yanlış duyulanlar [{s["aday"]}] (beklenen -> duyulan):')
        for (b, d), sayi in s['farklar'].most_common(args.hatalar):
            print(f'  {sayi:3}  "{b}" -> "{d}"')

    if args.tablo:
        yeni = not os.path.exists(args.tablo)
        with open(args.tablo, 'a', encoding='utf-8') as f:
            f.write(('\n' + BASLIK if yeni else '') + ''.join(satir(s, etiket) for s in sonuclar))
        print(f'\nTabloya eklendi: {args.tablo}')
    if args.cikti:
        with open(args.cikti, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(sonuclar[0]['kayitlar'][0]))
            w.writeheader()
            for s in sonuclar:
                w.writerows(s['kayitlar'])
        print(f'Dosya başına sonuçlar: {args.cikti}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
