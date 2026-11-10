"""LoRA adaptorunu taban modelle birlestirir -> tek bir Hugging Face model klasoru.

    python3 -m finetune.train.birlestir --ad drone-0.6b
Cikti: finetune/models/<ad>/hf/ (safetensors). Sonra: finetune/train/disa_aktar.sh <ad>
"""
import argparse
import json
import os

import torch

from ..ortak import MODELLER


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ad', default='drone-0.6b')
    args = ap.parse_args(argv)

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    klasor = os.path.join(MODELLER, args.ad)
    with open(os.path.join(klasor, 'egitim_kaydi.json'), encoding='utf-8') as f:
        taban = json.load(f)['ayarlar']['taban']
    model = AutoModelForCausalLM.from_pretrained(taban, dtype=torch.float32)
    model = PeftModel.from_pretrained(model, os.path.join(klasor, 'lora')).merge_and_unload()
    model.save_pretrained(os.path.join(klasor, 'hf'))
    AutoTokenizer.from_pretrained(os.path.join(klasor, 'lora')).save_pretrained(os.path.join(klasor, 'hf'))
    print(f'birleştirildi: {klasor}/hf  (taban: {taban})')


if __name__ == '__main__':
    main()
