"""Gorev 4.2 (istege bagli): bir LLM'den yeni dogal soyleyisler iste, otomatik dogrula.

    python3 -m finetune.data_gen.llm_cesitle --url http://127.0.0.1:8080 --adet 20 \
        --cikti finetune/data/llm_cesitleme.jsonl
    python3 -m finetune.data_gen.uret --ek-veri finetune/data/llm_cesitleme.jsonl

OpenAI uyumlu her sunucuyla calisir (llama-server, vLLM, bulut API). Guclu bir model
kullan; kucuk yerel model bu is icin zayiftir. API anahtari gerekiyorsa ortam
degiskeninden okunur (LLM_API_KEY), koda yazilmaz.

Guvence (YOL_HARITASI 4.2): Modelden cumleyle birlikte parametreleri AYRI alanda
istiyoruz ama etiketi biz kuruyoruz: once biz rastgele parametre seceriz, modelden o
parametrelerle cumle yazmasini isteriz, sonra parametrenin cumlede gercekten gectigini
(normalize sonrasi) kontrol ederiz. Gecmeyen cumle atilir.
"""
import argparse
import json
import os
import random

import requests

from ..ortak import jsonl_yaz, normalize
from .doldur import doldur
from .kontrol import sorun
from .parametreler import YERLER, YONLER
from .sablonlar import SABLONLAR

ISTEK = """Bir drone'a Türkçe sesli komut veriliyor.
Aşağıdaki komutu {adet} FARKLI doğal Türkçe söyleyişle yaz.
Çeşitlilik: günlük dil, devrik cümle, kibar/emir kipi, dolgu kelimeli ("ya şey", "hadi"), kısa/uzun.
Komut: {aciklama}
Örnek söyleyiş: "{ornek}"
Kurallar: Sayıları ve yönleri AYNEN koru, yeni bilgi ekleme, başka komut ekleme.
Yalnızca JSON dizi döndür: ["cümle 1", "cümle 2", ...]"""


def yon_ve_yer_geciyor(norm, adim):
    """LLM yonu ya da yeri degistirmis mi? ("kuzey" istedik, "güney" yazdi -> at)"""
    if 'yon' in adim and YONLER[adim['yon']][1] not in norm and YONLER[adim['yon']][0] not in norm:
        return False
    if 'tur' in adim and not any(y.split()[0][:5] in norm for y in YERLER[adim['tur']]):
        return False
    return True


def iste(url, model, mesaj):
    basliklar = {}
    if os.environ.get('LLM_API_KEY'):
        basliklar['Authorization'] = f'Bearer {os.environ["LLM_API_KEY"]}'
    yanit = requests.post(f'{url.rstrip("/")}/v1/chat/completions', headers=basliklar, timeout=120, json={
        'model': model, 'temperature': 0.9, 'max_tokens': 1500,
        'messages': [{'role': 'user', 'content': mesaj}],
        'chat_template_kwargs': {'enable_thinking': False},
    })
    yanit.raise_for_status()
    metin = yanit.json()['choices'][0]['message']['content']
    return json.loads(metin[metin.find('['):metin.rfind(']') + 1])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--url', required=True)
    ap.add_argument('--model', default='yerel')
    ap.add_argument('--adet', type=int, default=20, help='her istekte kaç söyleyiş')
    ap.add_argument('--tur', type=int, default=3, help='her komut için kaç istek')
    ap.add_argument('--cikti', required=True)
    ap.add_argument('--tohum', type=int, default=7)
    args = ap.parse_args(argv)

    rng = random.Random(args.tohum)
    satirlar, atilan, gorulen = [], 0, set()
    for komut, sablonlar in SABLONLAR.items():
        for _ in range(args.tur):
            ornek, adim = doldur(rng, rng.choice(sablonlar), komut)
            aciklama = json.dumps(adim, ensure_ascii=False)
            try:
                istek = ISTEK.format(adet=args.adet, aciklama=aciklama, ornek=ornek)
                cumleler = iste(args.url, args.model, istek)
            except (requests.RequestException, ValueError, KeyError) as e:
                print(f'{komut}: istek başarısız ({e})')
                continue
            for c in cumleler:
                norm = normalize(c) if isinstance(c, str) else ''
                if norm and norm not in gorulen and sorun(norm, [adim]) is None \
                        and yon_ve_yer_geciyor(norm, adim):
                    gorulen.add(norm)
                    satirlar.append({'metin': c, 'beklenen': {'adimlar': [adim]}})
                else:
                    atilan += 1
            print(f'{komut}: toplam {len(satirlar)} geçerli, {atilan} atıldı', flush=True)
    jsonl_yaz(args.cikti, satirlar)
    print(f'{len(satirlar)} söyleyiş -> {args.cikti} (gözle kontrol etmeden eğitime koyma)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
