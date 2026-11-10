"""train/veri.py: kayip yalniz cevapta mi, prompt kullanimdakiyle ayni mi? (tokenizer yoksa atlanir)"""
import pytest

transformers = pytest.importorskip('transformers')
pytest.importorskip('torch')

from finetune.ortak import KISA_SISTEM_PROMPT, sohbet_ornegi  # noqa: E402
from finetune.train.veri import YOKSAY, ornegi_kodla, prompt_metni, yigin_yap  # noqa: E402


@pytest.fixture(scope='module')
def tokenizer():
    try:
        return transformers.AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B', local_files_only=True)
    except OSError:
        pytest.skip('Qwen3-0.6B indirilmemiş')


def test_prompt_dusunmesiz_ve_kisa(tokenizer):
    satir = sohbet_ornegi('500 m yüksel', [{'komut': 'yuksel', 'metre': 500.0}])
    p = prompt_metni(tokenizer, satir['messages'])
    assert KISA_SISTEM_PROMPT in p and '500 m yüksel' in p
    assert p.endswith('<|im_start|>assistant\n<think>\n\n</think>\n\n')     # llama-server ile ayni


def test_kayip_yalniz_cevapta(tokenizer):
    satir = sohbet_ornegi('500 m yüksel', [{'komut': 'yuksel', 'metre': 500.0}])
    o = ornegi_kodla(tokenizer, satir, 256)
    cevap = [t for t, e in zip(o['ids'], o['etiketler']) if e != YOKSAY]
    assert tokenizer.decode(cevap) == '{"adimlar":[{"komut":"yuksel","metre":500}]}<|im_end|>'
    assert o['etiketler'][0] == YOKSAY


def test_yigin_dolgusu(tokenizer):
    a = ornegi_kodla(tokenizer, sohbet_ornegi('in', [{'komut': 'in'}]), 256)
    iki_adim = [{'komut': 'yuksel', 'metre': 50.0}, {'komut': 'in'}]
    b = ornegi_kodla(tokenizer, sohbet_ornegi('önce 50 m yüksel sonra in', iki_adim), 256)
    g = yigin_yap([a, b], tokenizer.pad_token_id)
    assert g['input_ids'].shape == g['labels'].shape == g['attention_mask'].shape
    assert g['attention_mask'][0].sum() == len(a['ids'])
    assert (g['labels'][0, len(a['ids']):] == YOKSAY).all()                  # dolgu kayba girmez
