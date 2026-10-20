"""Gercek WebSocket sunucusu + sahte_telefon istemcisi (ROS'suz uctan uca)."""
import asyncio
import struct
import wave

from mobile_bridge import sahte_telefon
from mobile_bridge.cekirdek import Ayarlar, RosArayuzu, TelsizCekirdegi
from mobile_bridge.sunucu import TelsizSunucusu


class SahteRos(RosArayuzu):
    """Parser'i taklit eder: metin gelince 'komut' ve 'geri_bildirim' uretir."""

    def __init__(self):
        self.sunucu = None
        self.metinler, self.acil = [], 0

    def metin_yayinla(self, metin):
        self.metinler.append(metin)
        komut = {'metin': metin, 'kaynak': 'hizli_yol', 'kuyruga_ekle': False,
                 'adimlar': [{'komut': 'kalk'}], 'parser_ms': 0.1}
        self.sunucu.disaridan(self.sunucu.cekirdek.ros_komut, komut)
        self.sunucu.disaridan(self.sunucu.cekirdek.ros_geri_bildirim, 'yurutuyor', 'kalkıyorum')

    def acil_dur_yayinla(self):
        self.acil += 1

    def stt_baslat(self, konusma):
        # STT'yi baska bir thread'de calisiyormus gibi taklit et
        self.sunucu.disaridan(self.sunucu.cekirdek.stt_sonucu, konusma, 'kalk', 5.0)


def calistir(tmp_path, **istemci):
    ros = SahteRos()
    cekirdek = TelsizCekirdegi(ros, Ayarlar(token='T'), stt_hazir=True)
    sunucu = TelsizSunucusu(cekirdek, '127.0.0.1', 0)
    ros.sunucu = sunucu
    satirlar = []

    async def senaryo():
        gorev = asyncio.ensure_future(sunucu.calis())
        await sunucu.hazir_bekle()
        url = f'ws://127.0.0.1:{sunucu.port}/telsiz?token=T'
        await sahte_telefon.calistir(url, bekle_s=0.5, gercek_zaman=False,
                                     cikti=satirlar.append, **istemci)
        sunucu.durdur()
        await gorev

    asyncio.run(senaryo())
    return ros, '\n'.join(satirlar)


def test_metin_uctan_uca(tmp_path):
    ros, log = calistir(tmp_path, metin='kalk')
    assert ros.metinler == ['kalk']
    assert '"tip": "duyuldu"' in log and '"tip": "komut"' in log and 'kalkıyorum' in log


def test_wav_uctan_uca(tmp_path):
    yol = tmp_path / 'k.wav'
    with wave.open(str(yol), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack('<h', 500) * 16000)
    ros, log = calistir(tmp_path, wav=str(yol))
    assert '"tip": "isleniyor"' in log and '"sure_ms": 1000' in log
    assert ros.metinler == ['kalk'] and '"kaynak": "yer_stt"' in log


def test_acil_dur(tmp_path):
    ros, log = calistir(tmp_path, acil=True)
    # 1: ACIL DUR tusu, 2: operator baglantiyi kapatti (havada olabilir -> guvenli taraf)
    assert ros.acil == 2 and 'acil_dur' in log


def test_yanlis_yol_reddedilir(tmp_path):
    async def dene():
        cek = TelsizCekirdegi(SahteRos(), Ayarlar(token='T'))
        s = TelsizSunucusu(cek, '127.0.0.1', 0)
        g = asyncio.ensure_future(s.calis())
        await s.hazir_bekle()
        import websockets
        async with websockets.connect(f'ws://127.0.0.1:{s.port}/baska') as ws:
            try:
                await ws.recv()
            except websockets.ConnectionClosed as e:
                kod = e.rcvd.code
        s.durdur()
        await g
        return kod
    assert asyncio.run(dene()) == 4404
