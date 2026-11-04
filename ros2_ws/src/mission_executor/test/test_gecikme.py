from mission_executor.gecikme import GecikmeIzleyici

MS = 1_000_000
DUR = (0.0, 0.0, 0.0)


def test_t4_ilk_tik_t5_hiz_degisince():
    g = GecikmeIzleyici(esik_mps=0.2)
    assert g.baslat('msg', 0, DUR) is None
    assert g.tik(50 * MS, DUR) is None            # t4
    assert g.tik(100 * MS, (0.1, 0, 0)) is None   # esik alti
    o = g.tik(150 * MS, (0.5, 0, 0))
    assert (o.t3, o.t4, o.t5, o.sonuc) == (0, 50 * MS, 150 * MS, 'kabul')
    assert g.aktif is None


def test_dur_hiz_azalmasi_da_degisimdir():
    g = GecikmeIzleyici()
    g.baslat('msg', 0, (5.0, 0, 0))
    g.tik(50 * MS, (5.0, 0, 0))
    assert g.tik(100 * MS, (4.5, 0, 0)).t5 == 100 * MS


def test_hareketsiz_komut_zaman_asiminda_t5siz_kapanir():
    g = GecikmeIzleyici(zaman_asimi_s=1.0)
    g.baslat('msg', 0, DUR)
    g.tik(50 * MS, DUR)
    assert g.tik(900 * MS, DUR) is None
    o = g.tik(1001 * MS, DUR)
    assert o.t4 == 50 * MS and o.t5 == 0


def test_yeni_komut_eskisini_dondurur_ve_kapat():
    g = GecikmeIzleyici()
    g.baslat('a', 0, DUR)
    eski = g.baslat('b', 10 * MS, DUR)
    assert eski.msg == 'a' and eski.t5 == 0
    o = g.kapat('reddedildi')
    assert o.msg == 'b' and o.sonuc == 'reddedildi'
    assert g.kapat('reddedildi') is None
    assert g.tik(20 * MS, DUR) is None
