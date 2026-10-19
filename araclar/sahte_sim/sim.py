"""ROS/PX4 olmadan mission_executor + command_parser'i uctan uca dener.

rclpy, px4_msgs ve drone_interfaces yerine stubs/ altindaki sahte modulleri,
PX4 yerine basit bir arac modelini (Arac) kullanir. Gercek simulasyonun yerini
TUTMAZ; durum makinesi / kuyruk / guvenlik mantigindaki hatalari erken yakalar.

    python3 araclar/sahte_sim/sim.py
"""
import math
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BURASI, '..', '..', 'ros2_ws', 'src')
sys.path[:0] = [os.path.join(BURASI, 'stubs'), os.path.join(SRC, 'mission_executor'),
                os.path.join(SRC, 'command_parser')]
from rclpy.node import WORLD
from px4_msgs.msg import *
from drone_interfaces.msg import CommandList, DroneCommand
from std_msgs.msg import Empty, String

WORLD['px4_out'] = ['/fmu/out/vehicle_local_position', '/fmu/out/vehicle_status_v1',
                    '/fmu/out/vehicle_global_position', '/fmu/out/battery_status', '/fmu/out/vehicle_land_detected']

class Arac:
    def __init__(s):
        s.x=s.y=s.z=0.; s.yaw=0.; s.v=(0,0,0); s.armed=False; s.nav=4; s.landed=True
        s.sp=None; s.son_sp=-1; s.son_mod=-1
        sub = WORLD['topics'].setdefault
        sub('/fmu/in/trajectory_setpoint', []).append(s.sp_cb)
        sub('/fmu/in/offboard_control_mode', []).append(s.mod_cb)
        sub('/fmu/in/vehicle_command', []).append(s.cmd_cb)
    def sp_cb(s, m): s.sp = m; s.son_sp = WORLD['t']
    def mod_cb(s, m): s.son_mod = WORLD['t']
    def cmd_cb(s, m):
        c = m.command
        if c == 176 and m.param2 == 6:
            if WORLD['t'] - s.son_mod < 0.5e9 and s.sp: s.nav = 14
            else: print('!! offboard reddedildi: akış yok')
        elif c == 400: s.armed = m.param1 == 1
        elif c == 21: s.nav = 18
        elif c == 20: s.nav = 5
    def adim(s, dt):
        ox, oy, oz = s.x, s.y, s.z
        if s.nav == 14 and s.armed and WORLD['t'] - s.son_mod > 0.5e9:
            print('!! FAILSAFE: offboard akışı kesildi'); s.nav = 4
        if s.armed:
            if s.nav == 14 and s.sp:
                tx, ty, tz = s.sp.position
                s.x += max(-5*dt, min(5*dt, tx-s.x)); s.y += max(-5*dt, min(5*dt, ty-s.y)); s.z += max(-3*dt, min(3*dt, tz-s.z))
                dy = (s.sp.yaw - s.yaw + math.pi) % (2*math.pi) - math.pi
                s.yaw += max(-1.5*dt, min(1.5*dt, dy))
            elif s.nav == 18: s.z += 1.5*dt
            elif s.nav == 5:
                d = math.hypot(s.x, s.y)
                if d > 0.3: s.x -= 5*dt*s.x/d; s.y -= 5*dt*s.y/d
                else: s.z += 1.5*dt
            if s.z < -0.2: s.landed = False
            if s.z >= 0 and s.nav in (18, 5) or (s.z >= 0 and not s.landed and s.nav != 14):
                s.z = 0; s.landed = True; s.armed = False; s.nav = 4
            s.z = min(s.z, 0)
        s.v = ((s.x-ox)/dt, (s.y-oy)/dt, (s.z-oz)/dt)
        for t, m in [('/fmu/out/vehicle_local_position', VehicleLocalPosition(x=s.x, y=s.y, z=s.z, vx=s.v[0], vy=s.v[1], vz=s.v[2], heading=s.yaw)),
                     ('/fmu/out/vehicle_status_v1', VehicleStatus(arming_state=2 if s.armed else 1, nav_state=s.nav)),
                     ('/fmu/out/vehicle_land_detected', VehicleLandDetected(landed=s.landed))]:
            for cb in WORLD['topics'].get(t, []): cb(m)

WORLD['params'] = {'max_irtifa': 600.0}
from mission_executor.executor_node import ExecutorNode
from command_parser.parser_node import ParserNode
WORLD['params']['llm_acik'] = False
ex = ExecutorNode()
pa = ParserNode()
arac = Arac()
fb = []
WORLD['topics'].setdefault('/drone/feedback', []).append(lambda m: fb.append((WORLD['t'], m.durum, m.mesaj)))

def calis(sn):
    dt = 0.01
    for _ in range(int(sn/dt)):
        WORLD['t'] += int(dt*1e9)
        arac.adim(dt)
        for t in WORLD['timers']:
            if t.on and WORLD['t'] >= t.next:
                t.next = WORLD['t'] + int(t.period*1e9); t.cb()

def metin(s):
    print(f'\n>>> "{s}"')
    for cb in WORLD['topics']['/voice/text']: cb(String(data=s))

def komut(*adimlar, ekle=False):
    print(f'\n>>> komut {adimlar}')
    msg = CommandList(adimlar=[DroneCommand(**a) for a in adimlar], kuyruga_ekle=ekle, kaynak='terminal')
    for cb in WORLD['topics']['/drone/command']: cb(msg)

def poz(): return f'x={arac.x:.1f} y={arac.y:.1f} irtifa={-arac.z:.1f} yaw={math.degrees(arac.yaw):.0f} arm={arac.armed} nav={arac.nav} durum={ex.durum}'

def bekle_bitis(maks=120):
    for _ in range(int(maks/0.5)):
        calis(0.5)
        if ex.aktif is None and not ex.kuyruk: break
    print('   ', poz())

calis(2)
komut({'komut':'git_yon','yon':'ileri','metre':5.0}); calis(1)   # yerde -> red
komut({'komut':'kalk','metre':10.0}); bekle_bitis()
assert abs(arac.z + 10) < 0.6 and arac.armed
komut({'komut':'yuksel','metre':5000.0}); calis(1); assert abs(arac.z + 10) < 0.6
komut({'komut':'yuksel','metre':50.0}); bekle_bitis(); assert abs(arac.z + 60) < 0.6
komut({'komut':'alcal','metre':50.0}); bekle_bitis()
metin('sağa doksan derece dön'); bekle_bitis()
metin('ileri 20 metre git'); bekle_bitis(); assert abs(arac.y - 20) < 0.6 and abs(arac.x) < 0.6
metin('kuzeye 100 metre git'); calis(3); print('   hareket ortasi', poz())
metin('dur'); calis(1.5); x1 = arac.x; calis(2); print('   dur sonrasi', poz()); assert abs(arac.x - x1) < 0.3 and ex.aktif is None
komut({'komut':'yuksel','metre':10.0}, {'komut':'git_yon','yon':'bati','metre':10.0}); bekle_bitis()
assert abs(arac.z + 20) < 0.6
metin('sonra 3 saniye bekle'); metin('sonra eve dön'); bekle_bitis()
assert not arac.armed and math.hypot(arac.x, arac.y) < 1
print('\n>>> 10 dakika boşta (offboard akışı kesilmemeli)')
komut({'komut':'kalk'}); bekle_bitis(); calis(600); print('   ', poz()); assert arac.nav == 14
metin('in'); bekle_bitis(); assert not arac.armed
print('\nGERI BILDIRIMLER:')
for t, d, m in fb: print(f'{t/1e9:7.2f} {d:11} {m}')
print('\nTUM KONTROLLER GECTI')
