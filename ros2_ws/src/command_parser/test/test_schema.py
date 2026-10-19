import pytest

from command_parser.schema import (
    KOMUT_SEMASI, KOMUTLAR, SemaHatasi, bilinmiyor_mu, dogrula, kanonik, msg_alanlarina,
)


def test_semada_tum_komutlar_var():
    secenekler = KOMUT_SEMASI['properties']['adimlar']['items']['anyOf']
    assert [s['properties']['komut']['const'] for s in secenekler] == list(KOMUTLAR)


def test_dogrula_gecerli():
    adimlar = dogrula({'adimlar': [{'komut': 'yuksel', 'metre': 50},
                                   {'komut': 'git_yon', 'yon': 'kuzey', 'metre': 2e2}]})
    assert adimlar == [{'komut': 'yuksel', 'metre': 50.0},
                       {'komut': 'git_yon', 'yon': 'kuzey', 'metre': 200.0}]


@pytest.mark.parametrize('veri', [
    {},
    {'adimlar': []},
    {'adimlar': [{'komut': 'zipla'}]},
    {'adimlar': [{'komut': 'yuksel'}]},
    {'adimlar': [{'komut': 'yuksel', 'metre': '50'}]},
    {'adimlar': [{'komut': 'yuksel', 'metre': 50, 'yon': 'kuzey'}]},
    {'adimlar': [{'komut': 'don', 'yon': 'kuzey', 'derece': 90}]},
    {'adimlar': [{'komut': 'git_yon', 'yon': 'yukari', 'metre': 5}]},
    {'adimlar': [{'komut': 'in'}] * 6},
])
def test_dogrula_gecersiz(veri):
    with pytest.raises(SemaHatasi):
        dogrula(veri)


def test_yardimcilar():
    assert bilinmiyor_mu([{'komut': 'kalk'}, {'komut': 'bilinmiyor'}])
    assert msg_alanlarina({'komut': 'kalk', 'irtifa_m': 20.0}) == {'komut': 'kalk', 'metre': 20.0}
    assert kanonik([{'metre': 50, 'komut': 'yuksel'}]) == kanonik([{'komut': 'yuksel', 'metre': 50}])
