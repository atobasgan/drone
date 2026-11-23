"""Ortak veri tipleri: bulunan yer ve harita hatasi."""
from dataclasses import dataclass


class HaritaHatasi(RuntimeError):
    """Servise ulasilamadi, zaman asimi, gecersiz cevap... Kullaniciya mesaj olarak gider."""


@dataclass
class Yer:
    ad: str             # "Gazi Hastanesi" (adi yoksa tur adi: "hastane")
    enlem: float
    boylam: float
    mesafe_m: float     # aramanin yapildigi noktaya uzaklik
    kaynak: str         # osm | google
