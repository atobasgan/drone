import math

import pytest

from mission_executor import geo


def yakin(a, b, tol=1e-6):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def test_govde_to_ned_kuzeye_bakarken():
    assert yakin(geo.govde_to_ned(10, 0, 0.0), (10, 0))
    assert yakin(geo.govde_to_ned(0, 10, 0.0), (0, 10))


def test_govde_to_ned_doguya_bakarken_ileri_doguya_gider():
    assert yakin(geo.govde_to_ned(20, 0, math.pi / 2), (0, 20))
    # sag taraf guney olur
    assert yakin(geo.govde_to_ned(0, 5, math.pi / 2), (-5, 0))


@pytest.mark.parametrize('yon,beklenen', [
    ('kuzey', (30, 0)), ('guney', (-30, 0)), ('dogu', (0, 30)), ('bati', (0, -30)),
])
def test_dunya_yonleri_yaw_dan_bagimsiz(yon, beklenen):
    assert yakin(geo.yon_to_ned(yon, 30, 1.234), beklenen)


def test_bilinmeyen_yon():
    with pytest.raises(ValueError):
        geo.yon_to_ned('yukari', 5, 0)


def test_aci_sar():
    assert abs(geo.aci_sar(3 * math.pi / 2) - (-math.pi / 2)) < 1e-9
    assert abs(geo.aci_sar(-3 * math.pi / 2) - (math.pi / 2)) < 1e-9


ANKARA = (39.9208, 32.8541)


def test_referans_noktasi_orijin():
    assert yakin(geo.enlem_boylam_to_ned(*ANKARA, *ANKARA), (0, 0))


def test_kuzeydeki_nokta_pozitif_x():
    # 0.01 derece enlem ~ 1112 m
    x, y = geo.enlem_boylam_to_ned(ANKARA[0] + 0.01, ANKARA[1], *ANKARA)
    assert 1100 < x < 1125 and abs(y) < 1


def test_dogudaki_nokta_pozitif_y():
    x, y = geo.enlem_boylam_to_ned(ANKARA[0], ANKARA[1] + 0.01, *ANKARA)
    assert 840 < y < 860 and abs(x) < 5


def test_gidis_donus():
    lat, lon = geo.ned_to_enlem_boylam(500.0, -300.0, *ANKARA)
    assert yakin(geo.enlem_boylam_to_ned(lat, lon, *ANKARA), (500.0, -300.0), tol=1e-3)


def test_haversine_ile_tutarli():
    lat, lon = ANKARA[0] + 0.005, ANKARA[1] + 0.007
    x, y = geo.enlem_boylam_to_ned(lat, lon, *ANKARA)
    assert abs(math.hypot(x, y) - geo.haversine_m(*ANKARA, lat, lon)) < 0.5
