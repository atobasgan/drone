"""ROS'suz deneme sunucusu: gercek parser + guvenlik + sanal drone."""
import asyncio
import json
import time

import websockets

from command_parser.komut_cozucu import KomutCozucu
from mobile_bridge import protokol as p
from mobile_bridge.cekirdek import Ayarlar, TelsizCekirdegi
from mobile_bridge.deneme_sunucusu import SahteSTT, SanalDrone
from mobile_bridge.sunucu import TelsizSunucusu


class YavasCozucu(KomutCozucu):
    """LLM'i taklit eder: 'yavaş' iceren cumleler 0.5 sn surer."""

    def coz(self, ham_metin):
        if 'yavaş' in ham_metin:
            time.sleep(0.5)
            return super().coz('10 metre yüksel')
        return super().coz(ham_metin)


def senaryo(adimlar):
    drone = SanalDrone(YavasCozucu(), SahteSTT('kalk'), hiz_katsayisi=100)
    cek = TelsizCekirdegi(drone, Ayarlar(token='T'), stt_hazir=True)
    sunucu = TelsizSunucusu(cek, '127.0.0.1', 0)
    drone.sunucu = sunucu
    gelen = []

    async def calis():
        g = asyncio.ensure_future(sunucu.calis())
        await sunucu.hazir_bekle()
        async with websockets.connect(f'ws://127.0.0.1:{sunucu.port}/telsiz') as ws:
            await ws.send(p.json_yaz('merhaba', token='T'))

            async def dinle():
                async for ham in ws:
                    gelen.append(json.loads(ham))
            d = asyncio.ensure_future(dinle())
            for adim in adimlar:
                if isinstance(adim, float):
                    await asyncio.sleep(adim)
                else:
                    await ws.send(adim)
            await asyncio.sleep(0.8)
            d.cancel()
        sunucu.durdur()
        await g

    asyncio.run(calis())
    return drone, gelen


def tipte(gelen, tip, **kosul):
    return [m for m in gelen if m['tip'] == tip and all(m.get(k) == v for k, v in kosul.items())]


def test_gercek_parser_ve_guvenlik():
    drone, gelen = senaryo([p.json_yaz('metin', id=1, metin='kalk'), 0.3,
                            p.json_yaz('metin', id=2, metin='beş yüz metre yüksel')])
    assert tipte(gelen, 'komut', id=1)[0]['adimlar'] == [{'komut': 'kalk'}]
    assert tipte(gelen, 'geri_bildirim', id=1, durum='tamamlandi')
    red = tipte(gelen, 'geri_bildirim', id=2, durum='reddedildi')
    assert red and 'sınır' in red[0]['mesaj']
    assert drone.durum.havada and abs(drone.durum.poz.irtifa - 10) < 1e-6


def test_cozulurken_acil_dur_sonucu_iptal_eder():
    drone, gelen = senaryo([p.json_yaz('metin', id=1, metin='kalk'), 0.3,
                            p.json_yaz('metin', id=2, metin='yavaş bir şekilde biraz yüksel'), 0.1,
                            p.json_yaz('acil_dur')])
    assert not tipte(gelen, 'komut', id=2), 'iptal edilen komut yayınlanmamalı'
    iptal = tipte(gelen, 'geri_bildirim', id=2, durum='reddedildi')
    assert iptal and 'ACİL DUR' in iptal[0]['mesaj']
    assert abs(drone.durum.poz.irtifa - 10) < 1e-6, 'drone yükselmemeli'


def test_ses_sahte_stt_ile():
    _, gelen = senaryo([p.json_yaz('metin', id=0, metin='ısınma'),
                        p.json_yaz('ptt_basla', id=5),
                        p.ses_parcasi_yaz(5, 0, b'\x01\x00' * 8000),
                        p.json_yaz('ptt_bitti', id=5)])
    assert tipte(gelen, 'duyuldu', id=5)[0]['kaynak'] == 'yer_stt'
    assert tipte(gelen, 'komut', id=5)[0]['adimlar'] == [{'komut': 'kalk'}]
