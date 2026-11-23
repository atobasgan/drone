"""Faz 5 veri setini denetler (dogrula.py'nin genis semali hali).

    python3 -m finetune.data_gen.dogrula_harita            # finetune/data_faz5/
    python3 -m finetune.data_gen.dogrula_harita --ornek 30 # + gozle bakmak icin yere_git ornekleri

Kontroller: chat bicimi ve kisa sistem prompt'u; her cevap genis semaya uygun (yere_git dahil),
ad cumlede geciyor, sayi/acil kurallari; bolumler arasi ve elle yazilmis testlerle ayni cumle yok;
yere_git yer adlari bolumler arasinda ayrik; negatif orani %10-15.
"""
import argparse
import json
import os
import random
import sys

from ..ortak import KISA_SISTEM_PROMPT, el_yazisi_cumleler, jsonl_oku
from .uret_harita import BOLUMLER, VERI_FAZ5, harita_sorun


def denetle(klasor):
    hatalar = []
    bolumler = {b: jsonl_oku(os.path.join(klasor, f'{b}.jsonl')) for b in BOLUMLER}
    cumleler, adlar = {}, {}
    for b, satirlar in bolumler.items():
        adlar[b] = set()
        for i, s in enumerate(satirlar):
            m = s['messages']
            if [x['role'] for x in m] != ['system', 'user', 'assistant']:
                hatalar.append(f'{b}:{i} rol sirasi')
                continue
            if m[0]['content'] != KISA_SISTEM_PROMPT:
                hatalar.append(f'{b}:{i} sistem prompt farkli')
            adimlar = json.loads(m[2]['content'])['adimlar']
            neden = harita_sorun(m[1]['content'], adimlar)
            if neden:
                hatalar.append(f'{b}:{i} {neden}: {m[1]["content"]}')
            adlar[b] |= {a['ad'] for a in adimlar if a['komut'] == 'yere_git'}
        cumleler[b] = {s['messages'][1]['content'] for s in satirlar}
    for a, c in (('train', 'val'), ('train', 'test'), ('val', 'test')):
        if cumleler[a] & cumleler[c]:
            hatalar.append(f'{a} ile {c} arasinda {len(cumleler[a] & cumleler[c])} ayni cumle')
        if adlar[a] & adlar[c]:
            hatalar.append(f'{a} ile {c} ayni yer adini iceriyor: {sorted(adlar[a] & adlar[c])[:3]}')
    sizinti = set().union(*cumleler.values()) & el_yazisi_cumleler()
    if sizinti:
        hatalar.append(f'elle yazilmis test setinden {len(sizinti)} cumle')
    toplam = sum(len(s) for s in bolumler.values())
    negatif = sum(1 for s in bolumler.values() for x in s if 'bilinmiyor' in x['messages'][2]['content'])
    if not 0.10 <= negatif / toplam <= 0.15:
        hatalar.append(f'negatif orani %{negatif / toplam * 100:.1f} (hedef %10-15)')
    return hatalar


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--veri', default=VERI_FAZ5)
    ap.add_argument('--ornek', type=int, default=0)
    args = ap.parse_args(argv)
    hatalar = denetle(args.veri)
    if args.ornek:
        yeni = jsonl_oku(os.path.join(args.veri, 'train_harita.jsonl'))
        for s in random.Random(0).sample(yeni, min(args.ornek, len(yeni))):
            print(f'  {s["meta"]["ham"]!r:50} -> {s["messages"][2]["content"]}')
    for h in hatalar[:20]:
        print('HATA', h)
    print('TÜM KONTROLLER GEÇTİ' if not hatalar else f'{len(hatalar)} hata')
    return 1 if hatalar else 0


if __name__ == '__main__':
    sys.exit(main())
