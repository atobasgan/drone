"""Komut basina gecikme olcumu (Gorev 3.5, MIMARI 9.3): t3, t4, t5.

t0-t2 CommandList ile parser'dan gelir; yurutucu kendi damgalarini ekler:
  t3 komut yurutucuye ulasti
  t4 komuttan sonraki ilk setpoint yayinlandi
  t5 telemetride hizin ilk belirgin degisimi (PX4'un tepkisi)
ROS'tan bagimsizdir (zamanlar nanosaniye, hiz (vx, vy, vz) m/s).
"""
import math


class Olcum:

    def __init__(self, msg, t3_ns, hiz0):
        self.msg = msg          # CommandList
        self.t3 = t3_ns
        self.t4 = 0
        self.t5 = 0
        self.hiz0 = hiz0
        self.sonuc = 'kabul'


class GecikmeIzleyici:
    """Ayni anda tek komut izlenir; yeni komut gelince eskisi t5'siz kapanir."""

    def __init__(self, esik_mps=0.2, zaman_asimi_s=5.0):
        self.esik = esik_mps
        self.zaman_asimi_ns = int(zaman_asimi_s * 1e9)
        self.aktif = None

    def baslat(self, msg, t3_ns, hiz):
        """Yeni olcumu baslatir; yarim kalan onceki olcumu (yayinlanmak uzere) dondurur."""
        onceki, self.aktif = self.aktif, Olcum(msg, t3_ns, hiz)
        return onceki

    def kapat(self, sonuc):
        """Aktif olcumu verilen sonucla hemen bitirir (reddedildi, kuyrukta...)."""
        olcum, self.aktif = self.aktif, None
        if olcum is not None:
            olcum.sonuc = sonuc
        return olcum

    def tik(self, t_ns, hiz):
        """Her setpoint yayinindan sonra cagrilir; biten olcumu dondurur."""
        o = self.aktif
        if o is None:
            return None
        if not o.t4:
            o.t4 = t_ns
            return None
        if math.dist(hiz, o.hiz0) > self.esik:
            o.t5 = t_ns
        elif t_ns - o.t3 < self.zaman_asimi_ns:
            return None
        self.aktif = None
        return o
