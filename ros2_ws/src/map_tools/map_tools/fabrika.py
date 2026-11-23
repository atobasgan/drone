"""Parametredeki ada gore saglayici olusturur: 'osm' (ucretsiz) | 'google' (API anahtari).
onbellek_s > 0 ise saglayici OnbellekliSaglayici ile sarilir (0: onbellek yok)."""
from .onbellek import OnbellekliSaglayici


def saglayici_olustur(ad, zaman_asimi=8.0, onbellek_s=600.0):
    if ad == 'osm':
        from .osm import OSMSaglayici
        saglayici = OSMSaglayici(zaman_asimi=zaman_asimi)
    elif ad == 'google':
        from .google_places import GooglePlacesSaglayici
        saglayici = GooglePlacesSaglayici(zaman_asimi=zaman_asimi)
    else:
        raise ValueError(f'bilinmeyen harita sağlayıcısı: {ad} (osm | google)')
    return OnbellekliSaglayici(saglayici, onbellek_s) if onbellek_s > 0 else saglayici
