"""Gercek mobile_bridge node'u + parser + yurutucu + sanal PX4, ROS'suz.

Sahte telefon (WebSocket) "kalk", "20 metre yüksel" ve ACIL DUR gonderir;
drone'un sanal PX4'te gercekten kalktigi ve telefona komut / geri bildirim /
telemetri mesajlarinin dondugu dogrulanir.

    python3 araclar/sahte_sim/telsiz_sim.py
"""
import asyncio
import json
import os
import sys
import threading
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BURASI, '..', '..', 'ros2_ws', 'src')
sys.path.insert(0, os.path.join(SRC, 'mobile_bridge'))

import websockets  # noqa: E402

exec(open(os.path.join(BURASI, 'sim.py')).read().split('calis(2)\n')[0])  # noqa: S102  (sim ortamı)

os.environ['TELSIZ_TOKEN'] = 'SIM'
WORLD['params'].update({'port': 18765, 'host': '127.0.0.1', 'llm_acik': False})
from mobile_bridge import protokol as p  # noqa: E402
from mobile_bridge.bridge_node import BridgeNode  # noqa: E402

kopru = BridgeNode()
gelen = []
kilit = threading.Lock()


async def telefon(adimlar):
    async with websockets.connect('ws://127.0.0.1:18765/telsiz') as ws:
        await ws.send(p.json_yaz('merhaba', token='SIM', cihaz='sim'))

        async def dinle():
            async for ham in ws:
                with kilit:
                    gelen.append(json.loads(ham))
        d = asyncio.ensure_future(dinle())
        for a in adimlar:
            if isinstance(a, float):
                await asyncio.sleep(a)
            else:
                await ws.send(a)
        d.cancel()


def tipte(tip, **kosul):
    with kilit:
        return [m for m in gelen if m['tip'] == tip and all(m.get(k) == v for k, v in kosul.items())]


t = threading.Thread(target=lambda: asyncio.run(telefon([
    0.3,
    p.json_yaz('metin', id=1, metin='kalk'), 1.0,
    p.json_yaz('metin', id=2, metin='yirmi metre yüksel'), 1.0,
    p.json_yaz('acil_dur'), 1.5,
])), daemon=True)
time.sleep(0.3)
t.start()
bitis = time.time() + 6
while time.time() < bitis:          # sanal saat ~gercek zamanin 10 kati hizli ilerler
    calis(0.1)
    time.sleep(0.01)
t.join(timeout=2)

print('telefona gelen tipler:', sorted({m['tip'] for m in gelen}))
assert tipte('hos_geldin')[0]['rol'] == 'operator'
assert tipte('komut', id=1)[0]['adimlar'] == [{'komut': 'kalk'}]
assert tipte('komut', id=2)[0]['adimlar'] == [{'komut': 'yuksel', 'metre': 20}]
assert any(m['durum'] == 'yurutuyor' for m in tipte('geri_bildirim', id=1))
tel = [m for m in tipte('telemetri') if m.get('hazir')]
assert tel and max(m['irtifa'] for m in tel) > 5, 'telemetri drone kalktı göstermeli'
assert tipte('geri_bildirim', durum='acil_dur')
print('    ', poz())
print('TELSIZ SIMULASYONU GECTI')
os._exit(0)
