"""Gorev 4.5: LoRA fine-tune. transformers + peft; CPU'da da GPU'da da calisir.

    python3 -m finetune.train.egit                                   # Qwen3 0.6B
    python3 -m finetune.train.egit --taban Qwen/Qwen3-1.7B --ad drone-1.7b

Ayarlar (YOL_HARITASI 4.5 / MIMARI 6.3): LoRA r=16, alpha=16, lr=2e-4, 2 epoch,
max_seq 256, yigin 16, kayip yalniz cevapta. GPU'da Unsloth daha hizlidir; ayarlar ayni.

Cikti: finetune/models/<ad>/lora/  (en dusuk dogrulama kaybindaki adaptor)
       finetune/models/<ad>/egitim_kaydi.json (kayip egrisi, ayarlar, sure)
Sonraki adim: python3 -m finetune.train.birlestir --ad <ad>  ve  finetune/train/disa_aktar.sh <ad>
"""
import argparse
import json
import math
import os
import time

import torch

from ..ortak import MODELLER, VERI, jsonl_oku
from .veri import ornegi_kodla, tohumla, yigin_yap, yiginlar

LORA_HEDEFLERI = ['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']


def model_yukle(taban, r, alpha, cihaz, bellek_tasarrufu=True):
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(taban)
    tip = torch.bfloat16 if cihaz == 'cuda' else torch.float32
    model = AutoModelForCausalLM.from_pretrained(taban, dtype=tip).to(cihaz)
    if bellek_tasarrufu:
        # Gradient checkpointing: katman ara degerleri saklanmaz, geri yayilimda yeniden hesaplanir.
        # Bellek ~5 kat azalir, egitim ~%30 yavaslar. Kapali iken 16 GB RAM'de uzun yiginlar
        # surecin isletim sistemince oldurulmesine (OOM) yol acti.
        model.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
    ayar = LoraConfig(r=r, lora_alpha=alpha, lora_dropout=0.05, target_modules=LORA_HEDEFLERI,
                      task_type='CAUSAL_LM')
    model = get_peft_model(model, ayar)
    return tokenizer, model


def cevap_kaybi(model, g):
    """Kayip YALNIZ cevap tokenlerinde; sozcuk katmani (lm_head, 152 bin sozcuk) da yalniz orada calisir.

    model(**g).loss ile ayni sayiyi verir, ama her konum icin 152 binlik cikti hesaplamaz:
    kucuk modelde bu katman hesabin buyuk kismidir. Konum t, t+1'deki tokeni tahmin eder.
    """
    taban = model.get_base_model()            # LoRA katmanlari taban.model'in icinde
    gizli = taban.model(input_ids=g['input_ids'], attention_mask=g['attention_mask']).last_hidden_state
    hedef = g['labels'][:, 1:]
    secili = hedef != -100
    logits = taban.lm_head(gizli[:, :-1][secili])
    return torch.nn.functional.cross_entropy(logits.float(), hedef[secili]), int(secili.sum())


@torch.no_grad()
def dogrulama_kaybi(model, yiginlar_, pad_id, cihaz):
    model.eval()
    toplam = adet = 0
    for yigin in yiginlar_:
        kayip, n = cevap_kaybi(model, {k: v.to(cihaz) for k, v in yigin_yap(yigin, pad_id).items()})
        toplam += kayip.item() * n
        adet += n
    model.train()
    return toplam / adet


def egit(args):
    cihaz = 'cuda' if torch.cuda.is_available() else 'cpu'
    if cihaz == 'cpu' and args.thread:
        torch.set_num_threads(args.thread)
    rng = tohumla(args.tohum)
    tokenizer, model = model_yukle(args.taban, args.r, args.alpha, cihaz, not args.bellek_tasarrufu_yok)
    model.print_trainable_parameters()
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id

    def kodla(dosya):
        return [ornegi_kodla(tokenizer, s, args.max_uzunluk) for s in jsonl_oku(os.path.join(args.veri, dosya))]
    train, val = kodla('train.jsonl'), kodla('val.jsonl')
    val_yiginlari = yiginlar(val, args.yigin * 2)
    adim_basina_epoch = math.ceil(len(train) / args.yigin)
    toplam_adim = adim_basina_epoch * args.epoch
    if args.adim_siniri:
        toplam_adim = min(toplam_adim, args.adim_siniri)
    en_uzun = max(len(o['ids']) for o in train)
    print(f'cihaz {cihaz} | train {len(train)} | val {len(val)} | en uzun {en_uzun} token | {toplam_adim} adım',
          flush=True)

    from transformers import get_linear_schedule_with_warmup
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr,
                                  weight_decay=0.0)
    zamanlayici = get_linear_schedule_with_warmup(optimizer, int(toplam_adim * 0.05), toplam_adim)

    cikti = os.path.join(MODELLER, args.ad)
    os.makedirs(cikti, exist_ok=True)
    kayit = {'ayarlar': vars(args), 'egitim': [], 'dogrulama': []}
    en_iyi = dogrulama_kaybi(model, val_yiginlari, pad_id, cihaz)
    kayit['dogrulama'].append({'adim': 0, 'kayip': en_iyi})
    print(f'başlangıç doğrulama kaybı {en_iyi:.4f}', flush=True)
    t0 = time.time()
    adim = 0
    for epoch in range(args.epoch):
        for yigin in yiginlar(train, args.yigin, rng):
            if adim >= toplam_adim:
                break
            g = {k: v.to(cihaz) for k, v in yigin_yap(yigin, pad_id).items()}
            kayip, _ = cevap_kaybi(model, g)
            kayip.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            zamanlayici.step()
            optimizer.zero_grad()
            adim += 1
            if adim % args.log_adim == 0:
                kayit['egitim'].append({'adim': adim, 'kayip': kayip.item()})
                gecen = time.time() - t0
                kalan = gecen / adim * (toplam_adim - adim)
                print(f'epoch {epoch + 1} adım {adim}/{toplam_adim} kayıp {kayip.item():.4f} '
                      f'| {gecen / 60:.1f} dk, kalan ~{kalan / 60:.0f} dk', flush=True)
            if adim % args.dogrulama_adim == 0 or adim == toplam_adim:
                v = dogrulama_kaybi(model, val_yiginlari, pad_id, cihaz)
                kayit['dogrulama'].append({'adim': adim, 'kayip': v})
                iyi = v < en_iyi
                print(f'  doğrulama kaybı {v:.4f}{"  (en iyi, kaydedildi)" if iyi else ""}', flush=True)
                if iyi:
                    en_iyi = v
                    model.save_pretrained(os.path.join(cikti, 'lora'))
                    tokenizer.save_pretrained(os.path.join(cikti, 'lora'))
    kayit['sure_dk'] = round((time.time() - t0) / 60, 1)
    kayit['en_iyi_dogrulama'] = en_iyi
    with open(os.path.join(cikti, 'egitim_kaydi.json'), 'w', encoding='utf-8') as f:
        json.dump(kayit, f, ensure_ascii=False, indent=1)
    print(f'bitti: {kayit["sure_dk"]} dk, en iyi doğrulama kaybı {en_iyi:.4f} -> {cikti}/lora')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--taban', default='Qwen/Qwen3-0.6B', help='Hugging Face model adı ya da klasör')
    ap.add_argument('--ad', default='drone-0.6b', help='finetune/models/<ad>/ altına yazılır')
    ap.add_argument('--veri', default=VERI)
    ap.add_argument('--r', type=int, default=16)
    ap.add_argument('--alpha', type=int, default=16)
    ap.add_argument('--lr', type=float, default=2e-4)
    ap.add_argument('--epoch', type=int, default=2)
    ap.add_argument('--yigin', type=int, default=16)
    ap.add_argument('--max-uzunluk', type=int, default=256)
    ap.add_argument('--dogrulama-adim', type=int, default=100)
    ap.add_argument('--log-adim', type=int, default=10)
    ap.add_argument('--thread', type=int, default=0, help='CPU thread sayısı (0 = varsayılan)')
    ap.add_argument('--tohum', type=int, default=42)
    ap.add_argument('--adim-siniri', type=int, default=0, help='duman testi: bu kadar adımdan sonra dur')
    ap.add_argument('--bellek-tasarrufu-yok', action='store_true',
                    help='gradient checkpointing kapalı: daha hızlı ama çok bellek (büyük GPU)')
    egit(ap.parse_args(argv))


if __name__ == '__main__':
    main()
