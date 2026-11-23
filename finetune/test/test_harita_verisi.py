"""Faz 5 (Gorev 5.4) veri uretimi: yonelme eki, genis kontrol, bolum ayrikligi, Faz 4 verisi korunuyor mu."""
import json

import pytest

from finetune.data_gen import harita_sablonlari as hs
from finetune.data_gen.uret_harita import harita_sorun, uret
from finetune.eval.olc_harita import harita_hata_turu
from finetune.ortak import normalize


@pytest.mark.parametrize('ad, beklenen', [
    ('anıtkabir', "anıtkabir'e"), ('atakule', "atakule'ye"), ('odtü', "odtü'ye"),
    ('gençlik parkı', "gençlik parkı'na"), ('kocatepe camii', "kocatepe camii'ne"),
    ('ulus meydanı', "ulus meydanı'na"), ('armada', "armada'ya"), ('liman', "liman'a"),
])
def test_yonelme(ad, beklenen):
    assert hs.yonelme(ad) == beklenen


def test_yer_adlari_kurallara_uyuyor():
    for ad in hs.YER_ADLARI:
        norm = normalize(ad)
        assert not any(t.isdigit() for t in norm), ad
        assert harita_sorun(f"{hs.yonelme(norm)} git", [{'komut': 'yere_git', 'ad': norm}]) is None, ad


def test_harita_sorun():
    assert harita_sorun("anıtkabir'e git", [{'komut': 'yere_git', 'ad': 'anıtkabir'}]) is None
    assert harita_sorun("anıtkabir'e git", [{'komut': 'yere_git', 'ad': 'atakule'}]) == 'ad cumlede yok'
    assert harita_sorun("kalkıp anıtkabir'e git", [{'komut': 'kalk'}, {'komut': 'yere_git', 'ad': 'anıtkabir'}]) \
        is None
    assert harita_sorun("10 m yükselip anıtkabir'e git",
                        [{'komut': 'yuksel', 'metre': 20}, {'komut': 'yere_git', 'ad': 'anıtkabir'}]).startswith('sayi')
    assert harita_sorun("30 anıtkabir'e git", [{'komut': 'yere_git', 'ad': 'anıtkabir'}]) == 'etikette olmayan sayi'
    assert harita_sorun("anıtkabir'e git", [{'komut': 'yere_git', 'ad': ''}]).startswith('sema')


@pytest.fixture(scope='module')
def veri():
    return uret(tohum=42)


def test_faz4_verisi_aynen_korunur(veri):
    from finetune.ortak import VERI, jsonl_oku
    sonuc, _, _ = veri
    for b in ('train', 'val', 'test'):
        assert sonuc[b][0] == jsonl_oku(f'{VERI}/{b}.jsonl')


def test_yer_adlari_ve_cumleler_bolumler_arasi_ayrik(veri):
    sonuc, _, adlar = veri
    assert not set(adlar['train']) & set(adlar['test']) and not set(adlar['val']) & set(adlar['test'])
    cumle = {b: {s['messages'][1]['content'] for s in sonuc[b][0] + sonuc[b][1]} for b in sonuc}
    assert not cumle['train'] & cumle['test'] and not cumle['train'] & cumle['val']
    test_adlari = {json.loads(s['messages'][2]['content'])['adimlar'][0].get('ad') for s in sonuc['test'][1]}
    egitim_adlari = {normalize(a) for a in adlar['train']}
    assert not (test_adlari - {None}) & egitim_adlari


def test_her_yeni_ornek_gecerli_ve_tekrarlanabilir(veri):
    sonuc, _, _ = veri
    for b in sonuc:
        for s in sonuc[b][1]:
            assert harita_sorun(s['messages'][1]['content'], json.loads(s['messages'][2]['content'])['adimlar']) \
                is None
    assert uret(tohum=42)[0]['test'][1] == sonuc['test'][1]
    komutlar = {k for s in sonuc['train'][1] for k in s['meta']['komutlar']}
    assert {'yere_git', 'bilinmiyor', 'kalk'} <= komutlar


def test_harita_hata_turu():
    b = [{'komut': 'yere_git', 'ad': 'odtü'}]
    assert harita_hata_turu(b, [{'komut': 'yere_git', 'ad': 'odtu'}]) == 'yer_adi'
    assert harita_hata_turu(b, [{'komut': 'yakin_yere_git', 'tur': 'okul'}]) == 'komut_yanlis'
    assert harita_hata_turu(b, b) is None
