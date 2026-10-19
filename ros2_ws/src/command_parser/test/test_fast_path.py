"""Gorev 2.2: 30 basit cumlenin hepsi dogru, 10 karmasik cumlede hepsi None."""
import time

import pytest

from command_parser.fast_path import acil_mi, coz
from command_parser.normalize import normalize

BASIT = [
    ('kalk', {'komut': 'kalk'}),
    ('kalkış yap', {'komut': 'kalk'}),
    ('havalan', {'komut': 'kalk'}),
    ('on metreye kalk', {'komut': 'kalk', 'irtifa_m': 10.0}),
    ('in', {'komut': 'in'}),
    ('iniş yap', {'komut': 'in'}),
    ('lütfen yere in', {'komut': 'in'}),
    ('beş yüz metre yüksel', {'komut': 'yuksel', 'metre': 500.0}),
    ('20 metre yukarı çık', {'komut': 'yuksel', 'metre': 20.0}),
    ('elli metre tırman', {'komut': 'yuksel', 'metre': 50.0}),
    ('yukarı 15 metre', {'komut': 'yuksel', 'metre': 15.0}),
    ('yirmi metre alçal', {'komut': 'alcal', 'metre': 20.0}),
    ('10 metre aşağı in', {'komut': 'alcal', 'metre': 10.0}),
    ('aşağı 5 metre', {'komut': 'alcal', 'metre': 5.0}),
    ('yüz metreye çık', {'komut': 'irtifaya_cik', 'metre': 100.0}),
    ('30 metreye in', {'komut': 'irtifaya_cik', 'metre': 30.0}),
    ('irtifayı elli metreye getir', {'komut': 'irtifaya_cik', 'metre': 50.0}),
    ('kuzeye 50 metre git', {'komut': 'git_yon', 'yon': 'kuzey', 'metre': 50.0}),
    ('güneye yüz metre git', {'komut': 'git_yon', 'yon': 'guney', 'metre': 100.0}),
    ('200 metre doğuya git', {'komut': 'git_yon', 'yon': 'dogu', 'metre': 200.0}),
    ('batıya 70 metre uç', {'komut': 'git_yon', 'yon': 'bati', 'metre': 70.0}),
    ('ileri 30 metre', {'komut': 'git_yon', 'yon': 'ileri', 'metre': 30.0}),
    ('15 metre geri git', {'komut': 'git_yon', 'yon': 'geri', 'metre': 15.0}),
    ('sağa 10 metre git', {'komut': 'git_yon', 'yon': 'sag', 'metre': 10.0}),
    ('sağa doksan derece dön', {'komut': 'don', 'yon': 'sag', 'derece': 90.0}),
    ('45 derece sola dön', {'komut': 'don', 'yon': 'sol', 'derece': 45.0}),
    ('sola dön', {'komut': 'don', 'yon': 'sol', 'derece': 90.0}),
    ('eve dön', {'komut': 'eve_don'}),
    ('beş saniye bekle', {'komut': 'bekle', 'saniye': 5.0}),
    ('dur', {'komut': 'dur'}),
    ('acil', {'komut': 'dur'}),
    ('hemen iptal', {'komut': 'dur'}),
]

KARMASIK = [
    'önce 20 metre yüksel sonra kuzeye 50 metre git',
    'kalk ve otuz metre ileri git',
    'biraz yükselsene kırk metre kadar',
    'yüksekliği iki yüz metreye ayarla',
    'batı tarafına doğru seksen metre uç',
    'kendi etrafında sağa kırk beş derece dön',
    'geldiğin yere geri dön',
    'en yakın hastaneye git',
    'bugün hava nasıl',
    'yüz metre yükselip doğuya iki yüz metre git',
    'geri dön',
    'ileri git',
]


@pytest.mark.parametrize('cumle,beklenen', BASIT)
def test_basit_cumleler(cumle, beklenen):
    assert coz(normalize(cumle)) == {'adimlar': [beklenen]}


@pytest.mark.parametrize('cumle', KARMASIK)
def test_karmasik_cumleler_llm_e_gider(cumle):
    assert coz(normalize(cumle)) is None


def test_sayilar():
    assert len(BASIT) >= 30 and len(KARMASIK) >= 10


def test_acil_kelime_kelime_bazinda():
    assert acil_mi('hemen dur')
    assert acil_mi('20 m yüksel sonra dur')
    assert not acil_mi('durum nedir')


def test_sure_5_ms_altinda():
    cumleler = [normalize(c) for c, _ in BASIT] + [normalize(c) for c in KARMASIK]
    t0 = time.perf_counter()
    for c in cumleler:
        coz(c)
    ortalama_ms = (time.perf_counter() - t0) * 1000 / len(cumleler)
    assert ortalama_ms < 5
