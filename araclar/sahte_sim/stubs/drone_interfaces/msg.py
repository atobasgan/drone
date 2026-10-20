from builtin_interfaces.msg import Time
class DroneCommand:
    def __init__(self, **kw):
        self.komut=''; self.metre=0.; self.derece=0.; self.yon=''; self.enlem=0.; self.boylam=0.; self.tur=''; self.saniye=0.; self.mps=0.
        self.__dict__.update(kw)
class CommandList:
    def __init__(self, **kw):
        self.t_konusma_bitti=Time(); self.t_metin_geldi=Time(); self.t_komut_hazir=Time()
        self.adimlar=[]; self.kuyruga_ekle=False; self.metin=''; self.kaynak=''
        self.__dict__.update(kw)
class Feedback:
    def __init__(self, durum='', mesaj=''): self.durum, self.mesaj = durum, mesaj
class AudioUtterance:
    def __init__(self, **kw):
        self.t_konusma_basladi=Time(); self.t_konusma_bitti=Time(); self.id=0; self.kaynak=''
        self.ornekleme_hz=0; self.ornekler=[]
        self.__dict__.update(kw)
