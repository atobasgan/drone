"""finetune/ icin ortak yollar ve bicimler.

Sistem prompt'u ve sema command_parser'dan ALINIR, kopyalanmaz: egitimdeki prompt
ile kullanimdaki prompt BIREBIR ayni olmali (YOL_HARITASI Gorev 4.7).
Calistirma: depo kokunden  python3 -m finetune.data_gen.uret
"""
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINETUNE = os.path.join(KOK, 'finetune')
VERI = os.path.join(FINETUNE, 'data')
MODELLER = os.path.join(FINETUNE, 'models')
sys.path.insert(0, os.path.join(KOK, 'ros2_ws', 'src', 'command_parser'))

from command_parser.normalize import normalize  # noqa: E402
from command_parser.prompt import KISA_SISTEM_PROMPT  # noqa: E402
from command_parser.schema import dogrula  # noqa: E402,F401 (kontrol.py buradan alir)

# Elle yazilmis test setleri: bunlarin cumleleri egitime ASLA girmez.
EL_YAZISI_TESTLER = [
    os.path.join(KOK, 'recordings', 'cumleler.jsonl'),
    os.path.join(KOK, 'ros2_ws', 'src', 'command_parser', 'data', 'metin_test_seti.jsonl'),
]


def sayi(deger):
    """50.0 -> 50, 1.5 -> 1.5 (JSON'da gereksiz '.0' token harcamasin)."""
    return int(deger) if float(deger).is_integer() else deger


def cevap_json(adimlar):
    """Modelin uretmesi gereken cevap: tek satir, bosluksuz, sabit anahtar sirasi."""
    temiz = [{k: (sayi(v) if isinstance(v, float) else v) for k, v in a.items()} for a in adimlar]
    return json.dumps({'adimlar': temiz}, ensure_ascii=False, separators=(',', ':'))


def sohbet_ornegi(kullanici, adimlar, **meta):
    """Chat-JSONL satiri (KAVRAMLAR/MIMARI 6.3 ADIM 1). 'meta' egitimde kullanilmaz."""
    return {
        'messages': [
            {'role': 'system', 'content': KISA_SISTEM_PROMPT},
            {'role': 'user', 'content': kullanici},
            {'role': 'assistant', 'content': cevap_json(adimlar)},
        ],
        'meta': meta,
    }


def jsonl_oku(yol):
    with open(yol, encoding='utf-8') as f:
        return [json.loads(s) for s in f if s.strip() and not s.startswith('#')]


def jsonl_yaz(yol, satirlar):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, 'w', encoding='utf-8') as f:
        for s in satirlar:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')


def el_yazisi_cumleler():
    """Elle yazilmis test cumlelerinin normalize halleri (sizinti kontrolu icin)."""
    return {normalize(o['metin']) for yol in EL_YAZISI_TESTLER for o in jsonl_oku(yol)}
