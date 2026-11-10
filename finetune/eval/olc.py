"""Gorev 4.4 / 4.6: bir modeli uc test setinde olcer, sonuc tablosuna ve hata dosyasina yazar.

    ./scripts/llama_server.sh &                                  # model calisiyor olmali
    python3 -m finetune.eval.olc --etiket qwen3-0.6b --ft hayir --quant Q4_K_M
    python3 -m finetune.eval.olc --etiket drone-0.6b --ft evet --quant Q4_K_M --kisa-prompt

Test setleri:
  sentetik  finetune/data/test.jsonl     egitimde gorulmemis SABLONLARDAN uretildi
  cumleler  recordings/cumleler.jsonl    elle yazilmis 107 cumle (egitime hic girmedi)
Mod: sadece_llm (hizli yol kapali: modelin kendisini olceriz) ve istenirse tam_hat.
Cikti: finetune/eval/sonuclar.md (tablo), finetune/eval/hatalar/<etiket>_<set>.txt
"""
import argparse
import datetime
import json
import os
import re
import sys

from ..ortak import FINETUNE, KOK
from .hata_turleri import hata_turu, ozet

from command_parser.degerlendir import degerlendir, veri_oku  # noqa: E402 (ortak yolu ekler)
from command_parser.komut_cozucu import KomutCozucu  # noqa: E402
from command_parser.llm_client import LLMIstemcisi  # noqa: E402
from command_parser.prompt import KISA_SISTEM_PROMPT, SISTEM_PROMPT  # noqa: E402

SETLER = {
    'sentetik': os.path.join(FINETUNE, 'data', 'test.jsonl'),
    'cumleler': os.path.join(KOK, 'recordings', 'cumleler.jsonl'),
}
TABLO = os.path.join(FINETUNE, 'eval', 'sonuclar.md')
BASLIK = ('| tarih | model | fine-tune | quant | prompt | test seti | mod | n | tam eşleşme % '
          '| komut % | parametre % | yanlış kabul % | LLM ort ms | LLM p95 ms | hata türleri |\n'
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')


def tabloya_yaz(satir):
    yeni = not os.path.exists(TABLO)
    with open(TABLO, 'a', encoding='utf-8') as f:
        if yeni:
            f.write('# Faz 4 sonuç tablosu\n\nÜretim: `finetune/eval/model_olc.sh` '
                    '(python3 -m finetune.eval.olc). Donanım etikette yazılı.\n\n' + BASLIK)
        f.write(satir)


def hatalari_yaz(yol, hatalar):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, 'w', encoding='utf-8') as f:
        for metin, norm, beklenen, uretilen, kaynak, hata in hatalar:
            f.write(f'[{hata_turu(beklenen, uretilen) or "diger"}] {metin}\n'
                    f'    beklenen: {json.dumps(beklenen, ensure_ascii=False)}\n'
                    f'    üretilen: {json.dumps(uretilen, ensure_ascii=False)} {hata}\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--etiket', required=True, help='tabloda görünecek model adı')
    ap.add_argument('--ft', default='hayir', help='fine-tune edildi mi (evet/hayir)')
    ap.add_argument('--quant', default='Q4_K_M')
    ap.add_argument('--kisa-prompt', action='store_true', help='fine-tune\'lu model: eğitimdeki kısa prompt')
    ap.add_argument('--url', default='http://127.0.0.1:8080')
    ap.add_argument('--set', action='append', choices=list(SETLER), help='varsayılan: hepsi')
    ap.add_argument('--tam-hat', action='store_true', help='hızlı yol açıkken de ölç')
    ap.add_argument('--max-tokens', type=int, default=128)
    ap.add_argument('--zaman-asimi', type=float, default=30.0,
                    help='ölçümde istek zaman aşımı (canlı sistemde 5 sn); yavaş CPU\'da doğruluğu bozmasın')
    args = ap.parse_args(argv)

    llm = LLMIstemcisi(url=args.url, max_tokens=args.max_tokens, zaman_asimi=args.zaman_asimi,
                       sistem_prompt=KISA_SISTEM_PROMPT if args.kisa_prompt else SISTEM_PROMPT)
    if not llm.saglikli():
        print(f'llama-server\'a ulaşılamadı: {args.url}', file=sys.stderr)
        return 1
    llm.isit()
    prompt = 'kısa' if args.kisa_prompt else 'few-shot'
    modlar = [('sadece_llm', False)] + ([('tam_hat', True)] if args.tam_hat else [])
    for set_adi in args.set or list(SETLER):
        ornekler = veri_oku(SETLER[set_adi])
        for mod, hizli_yol in modlar:
            cozucu = KomutCozucu(llm=llm, hizli_yol=hizli_yol, onbellek_boyutu=0)
            s = degerlendir(ornekler, cozucu)
            turler = ', '.join(f'{k} {n}' for k, n in ozet(s['hatalar']).most_common())
            oranlar = (f'{s["tam_eslesme"]:.1f} | {s["komut_dogrulugu"]:.1f} | {s["parametre_dogrulugu"]:.1f} '
                       f'| {s["yanlis_kabul"]:.1f}')
            print(f'{args.etiket:28} {set_adi:9} {mod:10} tam | komut | param | yanlış kabul: {oranlar} '
                  f'| LLM {s["llm_ort_ms"]:.0f} ms | {turler}', flush=True)
            tabloya_yaz(f'| {datetime.date.today()} | {args.etiket} | {args.ft} | {args.quant} | {prompt} '
                        f'| {set_adi} | {mod} | {s["n"]} | {oranlar} | {s["llm_ort_ms"]:.0f} '
                        f'| {s["llm_p95_ms"]:.0f} | {turler} |\n')
            dosya = re.sub(r'[^\w.-]+', '_', f'{args.etiket} {args.quant} {set_adi} {mod}').strip('_')
            hatalari_yaz(os.path.join(FINETUNE, 'eval', 'hatalar', f'{dosya}.txt'), s['hatalar'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
