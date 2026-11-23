"""DroneCommand / CommandList <-> sema bicimindeki sozluk (harita_node icin).

command_parser.schema'nin donusumlerini kullanir; yalnizca semada olmayan yere_git'i
(ad alani) kendisi ekler. Mesaj sinifi disaridan verilir: testlerde sahtesi kullanilir.
"""
from command_parser.schema import msg_alanlarina, msg_alanlarindan

KOPYALANAN_ALANLAR = ('t_konusma_bitti', 't_stt_bitti', 't_metin_geldi', 't_komut_hazir',
                      'kuyruga_ekle', 'metin', 'kaynak', 'ses_kaynagi')


def msg_to_adim(msg):
    if msg.komut == 'yere_git':
        return {'komut': 'yere_git', 'ad': msg.ad}
    alanlar = {a: getattr(msg, a) for a in ('komut', 'metre', 'derece', 'yon', 'enlem', 'boylam', 'tur',
                                            'saniye', 'mps')}
    return msg_alanlarindan(alanlar)


def adim_to_msg(adim, DroneCommand):
    msg = DroneCommand()
    for alan, deger in msg_alanlarina(adim).items():
        setattr(msg, alan, deger)
    return msg


def yeni_liste(eski, adimlar, CommandList, DroneCommand):
    """Zaman damgalari, metin, kaynak, kuyruga_ekle AYNEN tasinir (gecikme olcumu bozulmasin)."""
    yeni = CommandList()
    for alan in KOPYALANAN_ALANLAR:
        setattr(yeni, alan, getattr(eski, alan))
    yeni.adimlar = [adim_to_msg(a, DroneCommand) for a in adimlar]
    return yeni


def dur_mu(msg):
    return bool(msg.adimlar) and msg.adimlar[0].komut == 'dur'
