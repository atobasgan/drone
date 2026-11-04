from builtin_interfaces.msg import Time
class DroneCommand:
    def __init__(self, **kw):
        self.komut=''; self.metre=0.; self.derece=0.; self.yon=''; self.enlem=0.; self.boylam=0.; self.tur=''; self.saniye=0.; self.mps=0.
        self.__dict__.update(kw)
class CommandList:
    def __init__(self, **kw):
        self.t_konusma_bitti=Time(); self.t_stt_bitti=Time(); self.t_metin_geldi=Time(); self.t_komut_hazir=Time()
        self.adimlar=[]; self.kuyruga_ekle=False; self.metin=''; self.kaynak=''; self.ses_kaynagi=''
        self.__dict__.update(kw)
class Feedback:
    def __init__(self, durum='', mesaj=''): self.durum, self.mesaj = durum, mesaj
class VoiceText:
    def __init__(self, **kw):
        self.metin=''; self.kaynak=''; self.dosya=''; self.t_konusma_bitti=Time(); self.t_stt_bitti=Time(); self.konusma_s=0.
        self.__dict__.update(kw)
class LatencySample:
    def __init__(self, **kw):
        self.metin=''; self.kaynak=''; self.ses_kaynagi=''; self.sonuc=''
        for t in ('t0_konusma_bitti', 't1_stt_bitti', 't_metin_geldi', 't2_komut_hazir',
                  't3_yurutucu_aldi', 't4_ilk_setpoint', 't5_hiz_degisti'): setattr(self, t, Time())
        self.__dict__.update(kw)
