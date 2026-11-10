"""Uretilmis veri setini denetler (Gorev 4.1 - 4.3 KONTROL maddeleri).

    python3 -m finetune.data_gen.dogrula            # kontroller
    python3 -m finetune.data_gen.dogrula --ornek 50 # + gozle incelemek icin rastgele 50 ornek

Kontroller:
  - her satir chat bicimi, sistem prompt'u kullanimdakiyle ayni
  - cevap gecerli JSON ve semaya uygun; sayilar cumlede geciyor (kontrol.sorun)
  - bolumler arasinda ve elle yazilmis test setleriyle birebir ayni cumle yok
  - toplam >= 3000, negatif orani %10-15
"""
import argparse
import json
import os
import random
import sys

from ..ortak import KISA_SISTEM_PROMPT, VERI, el_yazisi_cumleler, jsonl_oku
from .kontrol import sorun


def denetle(veri_klasoru):
    hatalar = []
    bolumler = {ad: jsonl_oku(os.path.join(veri_klasoru, f'{ad}.jsonl')) for ad in ('train', 'val', 'test')}
    cumleler = {}
    for ad, satirlar in bolumler.items():
        for i, s in enumerate(satirlar):
            m = s['messages']
            if [x['role'] for x in m] != ['system', 'user', 'assistant']:
                hatalar.append(f'{ad}:{i} rol sirasi')
                continue
            if m[0]['content'] != KISA_SISTEM_PROMPT:
                hatalar.append(f'{ad}:{i} sistem prompt farkli')
            neden = sorun(m[1]['content'], json.loads(m[2]['content'])['adimlar'])
            if neden:
                hatalar.append(f'{ad}:{i} {neden}: {m[1]["content"]}')
        cumleler[ad] = {s['messages'][1]['content'] for s in satirlar}

    for a, b in (('train', 'val'), ('train', 'test'), ('val', 'test')):
        ortak = cumleler[a] & cumleler[b]
        if ortak:
            hatalar.append(f'{a} ile {b} arasinda {len(ortak)} ayni cumle, ör. {sorted(ortak)[:3]}')
    sizinti = (cumleler['train'] | cumleler['val'] | cumleler['test']) & el_yazisi_cumleler()
    if sizinti:
        hatalar.append(f'elle yazilmis test setinden {len(sizinti)} cumle: {sorted(sizinti)[:3]}')

    toplam = sum(len(s) for s in bolumler.values())
    negatif = sum(1 for s in bolumler.values() for x in s if 'bilinmiyor' in x['messages'][2]['content'])
    if toplam < 3000:
        hatalar.append(f'toplam {toplam} < 3000')
    if not 0.10 <= negatif / toplam <= 0.15:
        hatalar.append(f'negatif orani %{negatif / toplam * 100:.1f} (hedef %10-15)')
    return bolumler, toplam, negatif, hatalar


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--veri', default=VERI)
    ap.add_argument('--ornek', type=int, default=0, help='gözle kontrol için rastgele örnek sayısı')
    args = ap.parse_args(argv)

    bolumler, toplam, negatif, hatalar = denetle(args.veri)
    print(' | '.join(f'{ad}: {len(s)}' for ad, s in bolumler.items()),
          f'| toplam {toplam} | negatif %{negatif / toplam * 100:.1f}')
    if args.ornek:
        rng = random.Random(0)
        for s in rng.sample(bolumler['train'], args.ornek):
            ham, girdi, cevap = s['meta']['ham'], s['messages'][1]['content'], s['messages'][2]['content']
            print(f'  {ham!r:55} -> {girdi!r:45} {cevap}')
    for h in hatalar[:20]:
        print('HATA', h)
    print('TÜM KONTROLLER GEÇTİ' if not hatalar else f'{len(hatalar)} hata')
    return 1 if hatalar else 0


if __name__ == '__main__':
    sys.exit(main())
