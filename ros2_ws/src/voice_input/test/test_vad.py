import numpy as np

from voice_input.vad import CERCEVE, KonusmaAyirici


class SahteVAD:
    """Cercevenin ilk ornegi 1 ise konusma (olasilik 1), degilse sessizlik."""

    def __call__(self, cerceve):
        return float(cerceve[0])


def akis(*bolumler):
    """bolumler: (konusma_mi, cerceve_sayisi) ..."""
    return np.concatenate([np.full(n * CERCEVE, 1.0 if k else 0.0, np.float32) for k, n in bolumler])


def ayirici(**kw):
    # 32 ms cerceve: 400 ms ~ 12-13 cerceve, 250 ms ~ 8 cerceve, 200 ms ~ 6 cerceve
    return KonusmaAyirici(SahteVAD(), **kw)


def test_konusma_bitis_sessizliginden_sonra_biter():
    a = ayirici()
    assert a.besle(akis((0, 20), (1, 30), (0, 5))) == []
    assert a.konusuyor
    biten = a.besle(akis((0, 10)))
    assert len(biten) == 1
    # on kayit (6) + konusma (30) + birakilan ~100 ms sessizlik (3)
    assert len(biten[0].ornekler) == (6 + 30 + 3) * CERCEVE
    assert not a.konusuyor


def test_kisa_ses_atilir():
    a = ayirici()
    assert a.besle(akis((0, 10), (1, 3), (0, 30))) == []


def test_kisa_duraklama_konusmayi_bolmez():
    a = ayirici()
    biten = a.besle(akis((1, 15), (0, 6), (1, 15), (0, 20)))
    assert len(biten) == 1


def test_parca_parca_besleme_ayni_sonuc():
    x = akis((0, 5), (1, 20), (0, 20))
    tek = ayirici().besle(x)
    a = ayirici()
    parcali = []
    for i in range(0, len(x), 300):     # cerceve boyuna denk gelmeyen parcalar
        parcali += a.besle(x[i:i + 300])
    assert len(tek) == len(parcali) == 1
    assert np.array_equal(tek[0].ornekler, parcali[0].ornekler)


def test_uzun_konusma_zorla_kesilir_ve_bosalt():
    a = ayirici(max_konusma_s=1.0)          # ~31 cerceve
    biten = a.besle(akis((1, 40)))
    assert len(biten) == 1 and len(biten[0].ornekler) == 31 * CERCEVE
    kalan = a.bosalt()                      # konusma surdu: kalan 9 cerceve yeni parca
    assert len(kalan.ornekler) == 9 * CERCEVE
    assert a.bosalt() is None
