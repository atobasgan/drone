"""Faz 4 veri uretimi: etiketler dogru mu, kontroller calisiyor mu, bolumler sizdiriyor mu?"""
import json
import random

import pytest

from finetune.data_gen import cesitleme, negatifler, parametreler as p, sablonlar, uret
from finetune.data_gen.doldur import doldur
from finetune.data_gen.kontrol import sorun
from finetune.eval.hata_turleri import hata_turu
from finetune.ortak import cevap_json, normalize


@pytest.mark.parametrize('sayi, yazi', [
    (5, 'beş'), (15, 'on beş'), (100, 'yüz'), (150, 'yüz elli'), (1000, 'bin'),
    (1250, 'bin iki yüz elli'), (2.5, 'iki buçuk'), (0.5, 'yarım'),
])
def test_sayi_yaziyla(sayi, yazi):
    assert p.sayi_yaziyla(sayi) == yazi


def test_yaziyla_sayi_normalize_ile_geri_doner():
    for n in [1, 7, 12, 40, 99, 101, 345, 999, 1000, 2024, 1.5]:
        rakam = str(int(n)) if n == int(n) else str(n)
        assert normalize(p.sayi_yaziyla(n) + ' metre') == f'{rakam} m'


def test_doldur_etiketi_cumleyle_tutarli():
    rng = random.Random(0)
    for komut, liste in {**sablonlar.SABLONLAR}.items():
        for sablon in liste:
            cumle, adim = doldur(rng, sablon, komut)
            assert adim['komut'] == komut
            neden = sorun(normalize(cumle), [adim])
            assert neden in (None, 'acil kelime var (LLM\'e gitmez)') or neden.startswith('sayi'), (cumle, neden)


def test_kurallar():
    rng = random.Random(1)
    assert doldur(rng, '{sagsol} dön', 'don')[1]['derece'] == 90          # varsayilan 90
    assert doldur(rng, '{irtifa} metreye kalk', 'kalk')[1].keys() == {'komut', 'irtifa_m'}
    assert doldur(rng, '{irtifa} metreye çık', 'irtifaya_cik')[1].keys() == {'komut', 'metre'}
    assert doldur(rng, '{dakika} dakika bekle', 'bekle')[1]['saniye'] % 30 == 0


def test_kontrol_bozuk_ornekleri_yakalar():
    assert sorun('50 m yüksel', [{'komut': 'yuksel', 'metre': 50}]) is None
    assert sorun('51 m yüksel', [{'komut': 'yuksel', 'metre': 50}]).startswith('sayi')
    assert sorun('yere 10 ve 60 m in', [{'komut': 'in'}, {'komut': 'alcal', 'metre': 60}]).startswith('etikette')
    assert sorun('kalk ve orada dur', [{'komut': 'kalk'}]).startswith('acil')
    assert sorun('sağa dön', [{'komut': 'don', 'yon': 'sag', 'derece': 90}]) is None
    assert sorun('20 yaşındayım', [{'komut': 'bilinmiyor'}]) is None       # negatifte sayi serbest


def test_cevap_json_kisa_ve_sabit():
    assert cevap_json([{'komut': 'yuksel', 'metre': 50.0}]) == '{"adimlar":[{"komut":"yuksel","metre":50}]}'
    assert cevap_json([{'komut': 'alcal', 'metre': 1.5}]) == '{"adimlar":[{"komut":"alcal","metre":1.5}]}'


def test_sablon_bolmesi_sizdirmaz():
    b = uret.sablonlari_bol(random.Random(42))
    idler = {ad: {g[3] for g in b[ad]} for ad in ('train', 'val', 'test')}
    assert not idler['train'] & idler['test'] and not idler['train'] & idler['val']
    for komut in sablonlar.SABLONLAR:                         # her komuttan her bolumde sablon var
        for ad in ('train', 'val', 'test'):
            assert any(g[1] == komut for g in b[ad]), (komut, ad)


def test_cesitleme_ve_negatif_tutarliligi():
    assert set(cesitleme.CESITLEME) == set(sablonlar.SABLONLAR)
    tum = [c for c, _ in negatifler.hepsi()]
    assert len(tum) == len(set(tum)), 'negatif listesinde tekrar var'
    # "bekle" ve "olduğun yerde bekle" dur; ayni cumle negatif listesinde olmamali (celiskili etiket)
    dur_cumleleri = set(sablonlar.SABLONLAR['dur']) | set(cesitleme.CESITLEME['dur'])
    assert not dur_cumleleri & set(tum)


@pytest.mark.parametrize('beklenen, uretilen, tur', [
    ([{'komut': 'bilinmiyor'}], [{'komut': 'bekle', 'saniye': 60}], 'negatifi_kabul'),
    ([{'komut': 'yuksel', 'metre': 50}], [], 'komutu_kacirdi'),
    ([{'komut': 'yuksel', 'metre': 50}], [{'komut': 'irtifaya_cik', 'metre': 50}], 'goreli_mutlak'),
    ([{'komut': 'kalk'}], [{'komut': 'kalk'}, {'komut': 'in'}], 'adim_sayisi'),
    ([{'komut': 'git_yon', 'yon': 'kuzey', 'metre': 5}], [{'komut': 'git_yon', 'yon': 'guney', 'metre': 5}], 'yon'),
    ([{'komut': 'alcal', 'metre': 30}], [{'komut': 'alcal', 'metre': 20}], 'sayi'),
    ([{'komut': 'in'}], [{'komut': 'in'}], None),
])
def test_hata_turu(beklenen, uretilen, tur):
    assert hata_turu(beklenen, uretilen) == tur


def test_uretilen_veri_dosyalari_gecerli():
    """data/ altindaki dosyalar (git'teki) kontrolleri geciyor mu? (uret.py calistirilmissa)"""
    from finetune.data_gen.dogrula import denetle
    from finetune.ortak import VERI
    import os
    if not os.path.exists(os.path.join(VERI, 'train.jsonl')):
        pytest.skip('veri üretilmemiş')
    _, toplam, _, hatalar = denetle(VERI)
    assert not hatalar, hatalar[:3]
    assert toplam >= 3000
    satir = json.loads(open(os.path.join(VERI, 'test.jsonl'), encoding='utf-8').readline())
    assert satir['messages'][0]['role'] == 'system'


def test_ikinci_tur_test_bolumunu_degistirmez():
    """ek_sablonlar.py (Gorev 4.6) yalniz train'e girer: test/val iki turda AYNI olmali."""
    from finetune.data_gen import ek_sablonlar
    ilk = uret.sablonlari_bol(random.Random(42), ek=False)
    ikinci = uret.sablonlari_bol(random.Random(42), ek=True)
    assert ilk['test'] == ikinci['test'] and ilk['val'] == ikinci['val']
    eklenen = sum(len(v) for v in ek_sablonlar.EK_SABLONLAR.values())
    assert len(ikinci['train']) == len(ilk['train']) + eklenen
    neg1, neg2 = uret.negatif_bolumleri(random.Random(1), ek=False), uret.negatif_bolumleri(random.Random(1), ek=True)
    assert neg1['test'] == neg2['test'] and neg1['val'] == neg2['val']


def test_ek_sablonlar_gecerli():
    from finetune.data_gen import ek_sablonlar
    rng = random.Random(3)
    for komut, liste in ek_sablonlar.EK_SABLONLAR.items():
        for sablon in liste:
            cumle, adim = doldur(rng, sablon, komut)
            neden = sorun(normalize(cumle), [adim])
            assert neden is None or neden.startswith('sayi'), (cumle, neden)
    for cumle in ek_sablonlar.EK_NEGATIFLER:                  # negatifler komut kalibina benzemesin
        assert sorun(normalize(cumle), [{'komut': 'bilinmiyor'}]) is None
