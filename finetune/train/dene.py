"""Gorev 4.5 "birkac cumleyi elle dene": egitilmis adaptorla cumle -> JSON (llama-server'siz).

    python3 -m finetune.train.dene --ad drone-0.6b "beş yüz metre yüksel" "saat kaç"
Cumle once normalize edilir (kullanimdaki gibi), sonra modelin cevabi yazilir.
"""
import argparse
import os

import torch

from ..ortak import KISA_SISTEM_PROMPT, MODELLER, normalize
from .veri import prompt_metni

VARSAYILAN = ['beş yüz metre yüksel', 'yüz metreye çık', 'ya şey bi kırk metre alçalsana',
              'önce sağa dön sonra kuzeye elli metre git ardından in', 'saat kaç', 'en yakın hastaneye git']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cumleler', nargs='*')
    ap.add_argument('--ad', default='drone-0.6b')
    args = ap.parse_args(argv)

    from peft import AutoPeftModelForCausalLM
    from transformers import AutoTokenizer
    yol = os.path.join(MODELLER, args.ad, 'lora')
    tokenizer = AutoTokenizer.from_pretrained(yol)
    model = AutoPeftModelForCausalLM.from_pretrained(yol, dtype=torch.float32).eval()
    for cumle in args.cumleler or VARSAYILAN:
        mesajlar = [{'role': 'system', 'content': KISA_SISTEM_PROMPT},
                    {'role': 'user', 'content': normalize(cumle)}]
        girdi = tokenizer(prompt_metni(tokenizer, mesajlar), return_tensors='pt', add_special_tokens=False)
        with torch.no_grad():
            cikti = model.generate(**girdi, max_new_tokens=96, do_sample=False)
        cevap = tokenizer.decode(cikti[0][girdi['input_ids'].shape[1]:], skip_special_tokens=True)
        print(f'{cumle!r:55} -> {cevap.strip()}')


if __name__ == '__main__':
    main()
