"""Koordinat donusumleri (ROS'tan bagimsiz, birim test edilebilir).

PX4 yerel cercevesi NED'dir: x = kuzey, y = dogu, z = asagi (metre).
Yaw: 0 = kuzey, saat yonunde artar (radyan).
"""
import math

DUNYA_YARICAPI_M = 6371000.0

# git_yon icin dunyaya sabit yonler: (kuzey, dogu) birim vektoru
DUNYA_YONLERI = {
    'kuzey': (1.0, 0.0),
    'guney': (-1.0, 0.0),
    'dogu': (0.0, 1.0),
    'bati': (0.0, -1.0),
}
# Govdeye gore yonler: (ileri, sag) birim vektoru
GOVDE_YONLERI = {
    'ileri': (1.0, 0.0),
    'geri': (-1.0, 0.0),
    'sag': (0.0, 1.0),
    'sol': (0.0, -1.0),
}


def aci_sar(aci):
    """Aciyi [-pi, pi) araligina sarar."""
    return (aci + math.pi) % (2.0 * math.pi) - math.pi


def govde_to_ned(ileri, sag, yaw):
    """Govde eksenindeki (ileri, sag) yer degistirmeyi NED (kuzey, dogu)'ya cevirir."""
    c, s = math.cos(yaw), math.sin(yaw)
    kuzey = ileri * c - sag * s
    dogu = ileri * s + sag * c
    return kuzey, dogu


def yon_to_ned(yon, metre, yaw):
    """git_yon komutunun yonunu ve mesafesini NED (dx, dy)'ye cevirir."""
    if yon in DUNYA_YONLERI:
        k, d = DUNYA_YONLERI[yon]
        return k * metre, d * metre
    if yon in GOVDE_YONLERI:
        i, s = GOVDE_YONLERI[yon]
        return govde_to_ned(i * metre, s * metre, yaw)
    raise ValueError(f'bilinmeyen yon: {yon}')


def enlem_boylam_to_ned(lat, lon, ref_lat, ref_lon):
    """Enlem/boylami referans noktaya gore yerel NED (x kuzey, y dogu) metreye cevirir.

    PX4'un map_projection'i ile ayni azimutal esit uzaklikli izdusum.
    """
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    rlat, rlon = math.radians(ref_lat), math.radians(ref_lon)
    sin_lat, cos_lat = math.sin(lat_r), math.cos(lat_r)
    sin_ref, cos_ref = math.sin(rlat), math.cos(rlat)
    cos_dlon = math.cos(lon_r - rlon)

    arg = max(-1.0, min(1.0, sin_ref * sin_lat + cos_ref * cos_lat * cos_dlon))
    c = math.acos(arg)
    k = c / math.sin(c) if abs(c) > 1e-12 else 1.0

    x = k * (cos_ref * sin_lat - sin_ref * cos_lat * cos_dlon) * DUNYA_YARICAPI_M
    y = k * cos_lat * math.sin(lon_r - rlon) * DUNYA_YARICAPI_M
    return x, y


def ned_to_enlem_boylam(x, y, ref_lat, ref_lon):
    """enlem_boylam_to_ned'in tersi."""
    xr, yr = x / DUNYA_YARICAPI_M, y / DUNYA_YARICAPI_M
    rlat, rlon = math.radians(ref_lat), math.radians(ref_lon)
    sin_ref, cos_ref = math.sin(rlat), math.cos(rlat)
    c = math.hypot(xr, yr)
    if c < 1e-12:
        return ref_lat, ref_lon
    sin_c, cos_c = math.sin(c), math.cos(c)
    lat = math.asin(cos_c * sin_ref + (xr * sin_c * cos_ref) / c)
    lon = rlon + math.atan2(yr * sin_c, c * cos_ref * cos_c - xr * sin_ref * sin_c)
    return math.degrees(lat), math.degrees(lon)


def haversine_m(lat1, lon1, lat2, lon2):
    """Iki enlem/boylam arasi buyuk daire mesafesi (metre)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * DUNYA_YARICAPI_M * math.asin(math.sqrt(a))
