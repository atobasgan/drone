"""Chat-JSONL -> token dizileri. Egitim ve kullanim AYNI metni gormeli.

Kullanimda llama-server (--jinja, enable_thinking=false) modele sunu verir:
    <|im_start|>system\nDrone komutunu JSON'a çevir.<|im_end|>
    <|im_start|>user\n500 m yüksel<|im_end|>
    <|im_start|>assistant\n<think>\n\n</think>\n\n
Model buradan devam edip cevabi ve <|im_end|> yazar. Egitimde de prompt kismi
ayni sablonla kurulur; kayip YALNIZ cevap tokenlerinde hesaplanir (Gorev 4.5:
"sadece assistant cevabi uzerinden kayip"). Prompt tokenlerinin etiketi -100.
"""
import random

import torch

YOKSAY = -100          # PyTorch'un cross-entropy'si bu etiketleri atlar


def prompt_metni(tokenizer, mesajlar):
    """Sistem + kullanici -> modelin cevaba baslayacagi yere kadar olan metin."""
    return tokenizer.apply_chat_template(mesajlar[:2], tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)


def ornegi_kodla(tokenizer, satir, max_uzunluk):
    mesajlar = satir['messages']
    prompt_ids = tokenizer(prompt_metni(tokenizer, mesajlar), add_special_tokens=False)['input_ids']
    cevap_ids = tokenizer(mesajlar[2]['content'] + '<|im_end|>', add_special_tokens=False)['input_ids']
    ids = (prompt_ids + cevap_ids)[:max_uzunluk]
    etiketler = ([YOKSAY] * len(prompt_ids) + cevap_ids)[:max_uzunluk]
    return {'ids': ids, 'etiketler': etiketler}


def yigin_yap(ornekler, pad_id):
    """Ayni yigindaki ornekleri en uzununa gore sagdan doldurur."""
    uzun = max(len(o['ids']) for o in ornekler)
    ids = torch.full((len(ornekler), uzun), pad_id)
    etiket = torch.full((len(ornekler), uzun), YOKSAY)
    maske = torch.zeros((len(ornekler), uzun), dtype=torch.long)
    for i, o in enumerate(ornekler):
        n = len(o['ids'])
        ids[i, :n] = torch.tensor(o['ids'])
        etiket[i, :n] = torch.tensor(o['etiketler'])
        maske[i, :n] = 1
    return {'input_ids': ids, 'labels': etiket, 'attention_mask': maske}


def yiginlar(ornekler, yigin_boyu, rng=None):
    """Benzer uzunluktakileri ayni yigina koyar (dolgu az -> CPU'da hizli); sirayi karistirir."""
    sirali = sorted(ornekler, key=lambda o: len(o['ids']))
    parcalar = [sirali[i:i + yigin_boyu] for i in range(0, len(sirali), yigin_boyu)]
    if rng is not None:
        rng.shuffle(parcalar)
    return parcalar


def tohumla(tohum):
    random.seed(tohum)
    torch.manual_seed(tohum)
    return random.Random(tohum)
