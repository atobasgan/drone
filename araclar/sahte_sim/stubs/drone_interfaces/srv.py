class FindNearest:
    class Request:
        def __init__(self, **kw):
            self.tur = ''; self.ad = ''; self.enlem = 0.; self.boylam = 0.; self.yaricap_m = 0.
            self.__dict__.update(kw)

    class Response:
        def __init__(self, **kw):
            self.bulundu = False; self.yer_adi = ''; self.enlem = 0.; self.boylam = 0.
            self.mesafe_m = 0.; self.kaynak = ''; self.hata = ''
            self.__dict__.update(kw)
