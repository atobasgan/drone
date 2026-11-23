"""Gorev 5.4 olcumu: Faz 5 modeli eski test setlerinde GERILEDI MI, yere_git'i ogrendi mi?

    ./scripts/llama_server.sh &   (ya da: python3 -m finetune.eval.hf_sunucu --ad drone-0.6b-faz5 &)
    python3 -m finetune.eval.olc_harita --etiket drone-0.6b-faz5 --kisa-prompt --arka-uc hf-fp32

olc.py'nin aynisi; farklar: HaritaLLMIstemcisi / HaritaKomutCozucu (yere_git'i taniyan alt siniflar)
ve ucuncu test seti. Sonuc: finetune/eval/sonuclar_faz5.md (Faz 4 tablosuna dokunmaz).
  sentetik  finetune/data/test.jsonl            Faz 4 sentetik testi (gerileme)
  cumleler  recordings/cumleler.jsonl           elle yazilmis 107 cumle (gerileme)
  harita    finetune/data_faz5/test_harita.jsonl yere_git; yer adlari egitimde hic gecmedi
"""
import argparse
from collections import Counter
import datetime
import os
import re
import sys

from ..ortak import FINETUNE, KOK
from .hata_turleri import hata_turu
from .olc import BASLIK, hatalari_yaz

from command_parser.degerlendir import degerlendir, veri_oku  # noqa: E402
from command_parser.harita_komutlari import HaritaKomutCozucu, HaritaLLMIstemcisi  # noqa: E402
from command_parser.prompt import KISA_SISTEM_PROMPT, SISTEM_PROMPT  # noqa: E402

SETLER = {
    'sentetik': os.path.join(FINETUNE, 'data', 'test.jsonl'),
    'cumleler': os.path.join(KOK, 'recordings', 'cumleler.jsonl'),
    'harita': os.path.join(FINETUNE, 'data_faz5', 'test_harita.jsonl'),
}
TABLO = os.path.join(FINETUNE, 'eval', 'sonuclar_faz5.md')


def harita_hata_turu(beklenen, uretilen):
    """hata_turu + yere_git'te yanlis yer adi ('sayi' diye sayilmasin)."""
    if len(beklenen) == len(uretilen) and any(
            b['komut'] == u['komut'] == 'yere_git' and b.get('ad') != u.get('ad') for b, u in zip(beklenen, uretilen)):
        return 'yer_adi'
    return hata_turu(beklenen, uretilen)


def ozet(hatalar):
    return Counter(harita_hata_turu(b, u) or 'diger' for _, _, b, u, _, _ in hatalar)


def tabloya_yaz(satir):
    yeni = not os.path.exists(TABLO)
    with open(TABLO, 'a', encoding='utf-8') as f:
        if yeni:
            f.write('# Faz 5 sonuç tablosu (Görev 5.4)\n\nÜretim: `python3 -m finetune.eval.olc_harita`. '
                    '"quant" sütunu arka ucu yazar (hf-fp32: transformers, şema kısıtı yok).\n\n' + BASLIK)
        f.write(satir)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--etiket', required=True)
    ap.add_argument('--ft', default='evet')
    ap.add_argument('--arka-uc', default='Q4_K_M', help='tabloda quant sütunu: Q4_K_M, Q8_0, hf-fp32 ...')
    ap.add_argument('--kisa-prompt', action='store_true')
    ap.add_argument('--url', default='http://127.0.0.1:8080')
    ap.add_argument('--set', action='append', choices=list(SETLER), help='varsayılan: hepsi')
    ap.add_argument('--tam-hat', action='store_true')
    ap.add_argument('--max-tokens', type=int, default=128)
    ap.add_argument('--zaman-asimi', type=float, default=60.0)
    args = ap.parse_args(argv)

    llm = HaritaLLMIstemcisi(url=args.url, max_tokens=args.max_tokens, zaman_asimi=args.zaman_asimi,
                             sistem_prompt=KISA_SISTEM_PROMPT if args.kisa_prompt else SISTEM_PROMPT)
    if not llm.saglikli():
        print(f'LLM sunucusuna ulaşılamadı: {args.url}', file=sys.stderr)
        return 1
    prompt = 'kısa' if args.kisa_prompt else 'few-shot'
    modlar = [('sadece_llm', False)] + ([('tam_hat', True)] if args.tam_hat else [])
    for set_adi in args.set or list(SETLER):
        ornekler = veri_oku(SETLER[set_adi])
        for mod, hizli_yol in modlar:
            s = degerlendir(ornekler, HaritaKomutCozucu(llm=llm, hizli_yol=hizli_yol, onbellek_boyutu=0))
            turler = ', '.join(f'{k} {n}' for k, n in ozet(s['hatalar']).most_common())
            oranlar = (f'{s["tam_eslesme"]:.1f} | {s["komut_dogrulugu"]:.1f} | {s["parametre_dogrulugu"]:.1f} '
                       f'| {s["yanlis_kabul"]:.1f}')
            print(f'{args.etiket:24} {set_adi:9} {mod:10} tam | komut | param | yanlış kabul: {oranlar} '
                  f'| LLM {s["llm_ort_ms"]:.0f} ms | {turler}', flush=True)
            tabloya_yaz(f'| {datetime.date.today()} | {args.etiket} | {args.ft} | {args.arka_uc} | {prompt} '
                        f'| {set_adi} | {mod} | {s["n"]} | {oranlar} | {s["llm_ort_ms"]:.0f} '
                        f'| {s["llm_p95_ms"]:.0f} | {turler} |\n')
            dosya = re.sub(r'[^\w.-]+', '_', f'{args.etiket} {args.arka_uc} {set_adi} {mod}').strip('_')
            hatalari_yaz(os.path.join(FINETUNE, 'eval', 'hatalar', f'{dosya}.txt'), s['hatalar'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
