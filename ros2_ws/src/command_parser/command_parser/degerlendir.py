"""Metin test setinde dogruluk ve gecikme olcumu (Gorev 2.4 baseline).

    ros2 run command_parser degerlendir --veri <metin_test_seti.jsonl> --etiket qwen3-0.6b
    # ya da ROS'suz:
    python3 -m command_parser.degerlendir --sadece-llm --etiket qwen3-1.7b

Her satir: {"metin": "...", "beklenen": {"adimlar": [...]}}
Metrikler (MIMARI 6.3 ADIM 5): tam eslesme, komut dogrulugu, yanlis kabul
(alakasiz cumleye komut uretme), ortalama / p95 sure, kaynak dagilimi.
"""
import argparse
from collections import Counter
import datetime
import json
import os
import statistics
import sys

from .komut_cozucu import KomutCozucu
from .llm_client import LLMIstemcisi
from .prompt import KISA_SISTEM_PROMPT, SISTEM_PROMPT
from .schema import bilinmiyor_mu, kanonik


def varsayilan_veri():
    try:
        from ament_index_python.packages import get_package_share_directory
        return os.path.join(get_package_share_directory('command_parser'), 'data',
                            'metin_test_seti.jsonl')
    except Exception:  # ROS yok ya da paket kurulu degil: kaynak agacindan oku
        return os.path.join(os.path.dirname(__file__), '..', 'data', 'metin_test_seti.jsonl')


def veri_oku(yol):
    with open(yol, encoding='utf-8') as f:
        return [json.loads(satir) for satir in f if satir.strip() and not satir.startswith('#')]


def yuzdelik(degerler, p):
    if not degerler:
        return 0.0
    s = sorted(degerler)
    k = (len(s) - 1) * p / 100
    alt = int(k)
    ust = min(alt + 1, len(s) - 1)
    return s[alt] + (s[ust] - s[alt]) * (k - alt)


def degerlendir(ornekler, cozucu, ayrintili=False):
    tam = komut = yanlis_kabul = negatif = 0
    sureler, llm_sureler = [], []
    kaynaklar = Counter()
    hatalar = []
    for ornek in ornekler:
        beklenen = ornek['beklenen']['adimlar']
        beklenen_bos = bilinmiyor_mu(beklenen)
        cozum = cozucu.coz(ornek['metin'])
        sureler.append(cozum.sure_ms)
        if cozum.kaynak == 'llm':
            llm_sureler.append(cozum.llm_ms)
        kaynaklar[cozum.kaynak] += 1
        uretilen = cozum.adimlar

        if beklenen_bos:
            negatif += 1
            dogru = not uretilen
            yanlis_kabul += 0 if dogru else 1
            komut_dogru = dogru
        else:
            dogru = kanonik(uretilen) == kanonik(beklenen)
            komut_dogru = [a['komut'] for a in uretilen] == [a['komut'] for a in beklenen]
        tam += dogru
        komut += komut_dogru
        if not dogru:
            hatalar.append((ornek['metin'], cozum.metin, beklenen, uretilen, cozum.kaynak, cozum.hata))
        if ayrintili:
            print(f'{"OK " if dogru else "HATA"} [{cozum.kaynak:9}] {cozum.sure_ms:7.1f} ms  '
                  f'{ornek["metin"]}')

    n = len(ornekler)
    return {
        'n': n,
        'tam_eslesme': tam / n * 100,
        'komut_dogrulugu': komut / n * 100,
        'yanlis_kabul': (yanlis_kabul / negatif * 100) if negatif else 0.0,
        'ort_ms': statistics.mean(sureler),
        'p95_ms': yuzdelik(sureler, 95),
        'llm_ort_ms': statistics.mean(llm_sureler) if llm_sureler else 0.0,
        'llm_p95_ms': yuzdelik(llm_sureler, 95),
        'kaynaklar': dict(kaynaklar),
        'hatalar': hatalar,
    }


def rapor_yaz(sonuc, etiket):
    print(f'\n=== {etiket} ({sonuc["n"]} cümle) ===')
    print(f'tam eşleşme     : %{sonuc["tam_eslesme"]:.1f}')
    print(f'komut doğruluğu : %{sonuc["komut_dogrulugu"]:.1f}')
    print(f'yanlış kabul    : %{sonuc["yanlis_kabul"]:.1f}')
    print(f'süre (tüm hat)  : ort {sonuc["ort_ms"]:.1f} ms, p95 {sonuc["p95_ms"]:.1f} ms')
    print(f'süre (LLM)      : ort {sonuc["llm_ort_ms"]:.1f} ms, p95 {sonuc["llm_p95_ms"]:.1f} ms')
    print(f'kaynaklar       : {sonuc["kaynaklar"]}')
    if sonuc['hatalar']:
        print('\nHatalar:')
        for metin, norm, beklenen, uretilen, kaynak, hata in sonuc['hatalar']:
            print(f'- "{metin}" -> "{norm}" [{kaynak}] {hata}')
            print(f'    beklenen: {json.dumps(beklenen, ensure_ascii=False)}')
            print(f'    üretilen: {json.dumps(uretilen, ensure_ascii=False)}')


def tabloya_ekle(yol, sonuc, etiket, mod):
    yeni = not os.path.exists(yol)
    with open(yol, 'a', encoding='utf-8') as f:
        if yeni:
            f.write('| tarih | model/etiket | mod | n | tam eşleşme % | komut % | yanlış kabul % '
                    '| ort ms | p95 ms | LLM ort ms | LLM p95 ms |\n')
            f.write('|---|---|---|---|---|---|---|---|---|---|---|\n')
        f.write(f'| {datetime.date.today()} | {etiket} | {mod} | {sonuc["n"]} '
                f'| {sonuc["tam_eslesme"]:.1f} | {sonuc["komut_dogrulugu"]:.1f} '
                f'| {sonuc["yanlis_kabul"]:.1f} | {sonuc["ort_ms"]:.1f} | {sonuc["p95_ms"]:.1f} '
                f'| {sonuc["llm_ort_ms"]:.1f} | {sonuc["llm_p95_ms"]:.1f} |\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--veri', default=None, help='varsayılan: paketteki metin_test_seti.jsonl')
    ap.add_argument('--url', default='http://127.0.0.1:8080')
    ap.add_argument('--etiket', default='model', help='sonuç tablosunda görünecek ad')
    ap.add_argument('--sadece-llm', action='store_true',
                    help='hızlı yolu kapat: her cümle LLM\'e gitsin (baseline için)')
    ap.add_argument('--llm-yok', action='store_true', help='sadece hızlı yol')
    ap.add_argument('--kisa-prompt', action='store_true', help='fine-tune\'lu model (Faz 4)')
    ap.add_argument('--max-tokens', type=int, default=64)
    ap.add_argument('--tablo', help='sonucu bu markdown tablosuna ekle (ör. NOTLAR_sonuclar.md)')
    ap.add_argument('-v', '--ayrintili', action='store_true')
    args = ap.parse_args(argv)

    llm = None
    if not args.llm_yok:
        llm = LLMIstemcisi(url=args.url, max_tokens=args.max_tokens,
                           sistem_prompt=KISA_SISTEM_PROMPT if args.kisa_prompt else SISTEM_PROMPT)
        if not llm.saglikli():
            print(f'llama-server\'a ulaşılamadı: {args.url}', file=sys.stderr)
            return 1
        llm.isit()
    cozucu = KomutCozucu(llm=llm, hizli_yol=not args.sadece_llm, onbellek_boyutu=0)

    ornekler = veri_oku(args.veri or varsayilan_veri())
    sonuc = degerlendir(ornekler, cozucu, args.ayrintili)
    mod = 'sadece_llm' if args.sadece_llm else ('sadece_hizli_yol' if args.llm_yok else 'tam_hat')
    rapor_yaz(sonuc, f'{args.etiket} / {mod}')
    if args.tablo:
        tabloya_ekle(args.tablo, sonuc, args.etiket, mod)
        print(f'\nTabloya eklendi: {args.tablo}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
