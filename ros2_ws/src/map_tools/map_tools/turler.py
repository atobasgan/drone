"""Turkce yer turu -> harita servislerindeki karsiliklari.

Komut semasindaki "tur" degerleri (command_parser/schema.py YER_TURLERI) ile ayni anahtarlar.
  osm    : OpenStreetMap etiketleri (Overpass sorgusu), herhangi biri eslesirse yeterli
  google : Places API (New) "includedTypes"
  ad     : geri bildirimde kullanilan Turkce ad, yonelme hali ("hastaneye")
"""

TURLER = {
    'hastane': {'osm': ['amenity=hospital'], 'google': ['hospital'], 'ad': 'hastane'},
    'eczane': {'osm': ['amenity=pharmacy'], 'google': ['pharmacy'], 'ad': 'eczane'},
    'benzinlik': {'osm': ['amenity=fuel'], 'google': ['gas_station'], 'ad': 'benzinlik'},
    'polis': {'osm': ['amenity=police'], 'google': ['police'], 'ad': 'polis merkezi'},
    'itfaiye': {'osm': ['amenity=fire_station'], 'google': ['fire_station'], 'ad': 'itfaiye'},
    'okul': {'osm': ['amenity=school'], 'google': ['school'], 'ad': 'okul'},
    'park': {'osm': ['leisure=park'], 'google': ['park'], 'ad': 'park'},
    'market': {'osm': ['shop=supermarket', 'shop=convenience'], 'google': ['supermarket', 'grocery_store'],
               'ad': 'market'},
}


def tur_bilgisi(tur):
    if tur not in TURLER:
        raise KeyError(f'bilinmeyen yer türü: {tur}')
    return TURLER[tur]
