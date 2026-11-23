"""Faz 5: harita komutlari uctan uca, ROS/PX4/internet OLMADAN.

    python3 araclar/sahte_sim/sim_harita.py

sim.py ile ayni sahte rclpy/px4 altyapisi (stubs/), ama harita.launch.py'deki zincir:
    harita_parser_node ─/drone/command─> harita_node ─/drone/command_harita─> mission_executor
Harita servisi yerine sabit yerler donduren SahteSaglayici kullanilir (internet yok).
Gercek simulasyonun yerini TUTMAZ; siralama, iptal, red ve seyir mantigini dener.
"""
import math
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BURASI, '..', '..', 'ros2_ws', 'src')
sys.path[:0] = [os.path.join(BURASI, 'stubs')] + [
    os.path.join(SRC, p) for p in ('mission_executor', 'command_parser', 'map_tools')]
from drone_interfaces.msg import CommandList, DroneCommand  # noqa: E402
from mission_executor.geo import haversine_m  # noqa: E402
from px4_msgs.msg import VehicleLandDetected, VehicleLocalPosition, VehicleStatus  # noqa: E402
from rclpy.node import WORLD  # noqa: E402
from std_msgs.msg import Empty, String  # noqa: E402

REF = (39.9208, 32.8541)          # PX4 kalkis noktasi (stub VehicleLocalPosition ref_lat/ref_lon)
WORLD['px4_out'] = ['/fmu/out/vehicle_local_position', '/fmu/out/vehicle_status_v1',
                    '/fmu/out/vehicle_land_detected']
WORLD['params'] = {'max_irtifa': 600.0, 'llm_acik': False, 'seyir_irtifasi_m': 30.0, 'en_uzak_m': 1000.0}


def nokta(kuzey_m, dogu_m):
    """Kalkis noktasina gore metre -> enlem/boylam (kucuk mesafe yaklasimi)."""
    return (REF[0] + kuzey_m / 111320.0, REF[1] + dogu_m / (111320.0 * math.cos(math.radians(REF[0]))))


YERLER = {'hastane': ('Test Hastanesi', *nokta(300, 200)), 'park': ('Test Parkı', *nokta(-150, 100)),
          'eczane': ('Test Eczanesi', *nokta(0, -250))}
ISIMLER = {'Kızılay Meydanı': ('Kızılay Meydanı', *nokta(100, -300)), 'Anıtkabir': ('Anıtkabir', *nokta(500, -1700))}


class SahteSaglayici:
    ad = 'sahte'

    def _yer(self, kayit, enlem, boylam):
        from map_tools.yer import Yer
        if not kayit:
            return None
        ad, e, b = kayit
        return Yer(ad, e, b, haversine_m(enlem, boylam, e, b), 'sahte')

    def en_yakin(self, tur, enlem, boylam, yaricap_m):
        return self._yer(YERLER.get(tur), enlem, boylam)

    def ara(self, ad, enlem, boylam, yaricap_m):
        return self._yer(ISIMLER.get(ad), enlem, boylam)


class Arac:
    """Yalniz offboard ucus: setpoint'e 5 m/s yatay, 3 m/s dikey yaklasir (sim.py'deki modelin ozu)."""

    def __init__(s):
        s.x = s.y = s.z = 0.0
        s.armed, s.nav, s.landed, s.sp = False, 4, True, None
        top = WORLD['topics'].setdefault
        top('/fmu/in/trajectory_setpoint', []).append(lambda m: setattr(s, 'sp', m))
        top('/fmu/in/vehicle_command', []).append(s.cmd_cb)

    def cmd_cb(s, m):
        if m.command == 176 and m.param2 == 6:
            s.nav = 14
        elif m.command == 400:
            s.armed = m.param1 == 1
        elif m.command == 21:
            s.nav = 18

    def adim(s, dt):
        if s.armed and s.nav == 14 and s.sp:
            tx, ty, tz = s.sp.position
            s.x += max(-5 * dt, min(5 * dt, tx - s.x))
            s.y += max(-5 * dt, min(5 * dt, ty - s.y))
            s.z += max(-3 * dt, min(3 * dt, tz - s.z))
        elif s.armed and s.nav == 18:
            s.z = min(0.0, s.z + 1.5 * dt)
            if s.z >= 0:
                s.armed, s.nav = False, 4
        s.landed = s.z > -0.2 and not (s.armed and s.nav == 14 and s.sp and s.sp.position[2] < -0.3)
        for t, m in [('/fmu/out/vehicle_local_position', VehicleLocalPosition(x=s.x, y=s.y, z=s.z)),
                     ('/fmu/out/vehicle_status_v1', VehicleStatus(arming_state=2 if s.armed else 1, nav_state=s.nav)),
                     ('/fmu/out/vehicle_land_detected', VehicleLandDetected(landed=s.landed))]:
            for cb in WORLD['topics'].get(t, []):
                cb(m)


from command_parser.harita_parser_node import HaritaParserNode  # noqa: E402
from map_tools.harita_node import HaritaNode  # noqa: E402
from mission_executor.executor_node import ExecutorNode  # noqa: E402

ex = ExecutorNode()
# harita.launch.py'deki remapping: yurutucu /drone/command yerine /drone/command_harita dinler
ex_cb = WORLD['topics']['/drone/command'].pop()
WORLD['topics'].setdefault('/drone/command_harita', []).append(ex_cb)
pa = HaritaParserNode()
hn = HaritaNode(saglayici=SahteSaglayici(), thread=False)
arac = Arac()
fb, olcumler = [], []
WORLD['topics'].setdefault('/drone/feedback', []).append(lambda m: fb.append((m.durum, m.mesaj)))
WORLD['topics'].setdefault('/latency/olcum', []).append(olcumler.append)


def calis(sn):
    dt = 0.01
    for _ in range(int(sn / dt)):
        WORLD['t'] += int(dt * 1e9)
        arac.adim(dt)
        for t in WORLD['timers']:
            if t.on and WORLD['t'] >= t.next:
                t.next = WORLD['t'] + int(t.period * 1e9)
                t.cb()


def harita_isle():
    """harita_node'un isci thread'inin yaptigi: kuyruktakileri sirayla isle."""
    while not hn._kuyruk.empty():
        hn.isle(*hn._kuyruk.get())


def metin(s):
    print(f'\n>>> "{s}"')
    for cb in WORLD['topics']['/voice/text']:
        cb(String(data=s))


def komut(*adimlar):
    print(f'\n>>> komut {adimlar}')
    msg = CommandList(adimlar=[DroneCommand(**a) for a in adimlar], kaynak='terminal')
    for cb in WORLD['topics']['/drone/command']:
        cb(msg)


def bekle_bitis(maks=200):
    for _ in range(int(maks / 0.5)):
        calis(0.5)
        if ex.aktif is None and not ex.kuyruk:
            break
    print(f'    x={arac.x:.1f} y={arac.y:.1f} irtifa={-arac.z:.1f}')


def ned(yer):
    from mission_executor.geo import enlem_boylam_to_ned
    return enlem_boylam_to_ned(yer[1], yer[2], *REF)


def son_mesaj(durum):
    return next((m for d, m in reversed(fb) if d == durum), '')


calis(2)
komut({'komut': 'kalk', 'metre': 10.0})
bekle_bitis()
assert abs(arac.z + 10) < 0.6

# 1) en yakin hastane: hizli yol -> harita -> once 30 m'ye tirman, sonra git
metin('en yakın hastaneye git')
assert hn._bekleyen == 1 and ex.aktif is None, 'harita cozulmeden yurutucuye gitmemeli'
harita_isle()
calis(3)
assert -arac.z > 12 and math.hypot(arac.x, arac.y) < 5, 'once tirmanmali, yatay gitmemeli'
bekle_bitis()
hx, hy = ned(YERLER['hastane'])
assert abs(arac.x - hx) < 1 and abs(arac.y - hy) < 1 and abs(arac.z + 30) < 0.6
assert 'uzaktaki Test Hastanesi' in son_mesaj('bilgi'), fb
assert olcumler and olcumler[-1].kaynak == 'hizli_yol' and olcumler[-1].t2_komut_hazir.sec >= 0

# 2) siralama: harita aramasi beklerken gelen "sonra 5 metre yüksel" onu sollamaz
metin('en yakın parka git')
metin('sonra 5 metre yüksel')
assert hn._bekleyen == 2 and ex.aktif is None
harita_isle()
bekle_bitis()
px, py = ned(YERLER['park'])
assert abs(arac.x - px) < 1 and abs(arac.y - py) < 1 and abs(arac.z + 35) < 0.6

# 3) arama surerken "dur": gec gelen sonuc yurutulmez, dur aninda gecer
x0, y0 = arac.x, arac.y
metin('en yakın eczaneye git')
metin('dur')
harita_isle()
calis(5)
assert math.hypot(arac.x - x0, arac.y - y0) < 0.5, 'dur sonrasi eczaneye gitmemeli'
assert 'iptal' in son_mesaj('reddedildi'), fb

# 4) cok uzak / bulunamadi / servis yok: drone hic hareket etmez
komut({'komut': 'yere_git', 'ad': 'Anıtkabir'})
harita_isle()
calis(2)
assert 'sınır 1.0 km' in son_mesaj('reddedildi') and math.hypot(arac.x - x0, arac.y - y0) < 0.5
metin('en yakın itfaiyeye git')
harita_isle()
assert 'itfaiye bulunamadı' in son_mesaj('reddedildi')

# 5) yere_git isimle (LLM kapali: terminalden komut) ve normal komutlar beklemeden gecer
komut({'komut': 'yere_git', 'ad': 'Kızılay Meydanı'})
harita_isle()
bekle_bitis()
kx, ky = ned(ISIMLER['Kızılay Meydanı'])
assert abs(arac.x - kx) < 1 and abs(arac.y - ky) < 1
metin('10 metre alçal')
assert hn._bekleyen == 0 and ex.aktif is not None, 'harita disi komut beklememeli'
bekle_bitis()
assert abs(arac.z + 25) < 0.6

# 6) ACIL DUR topic'i de bekleyen harita aramasini iptal eder
metin('en yakın hastaneye git')
for cb in WORLD['topics']['/drone/emergency_stop']:
    cb(Empty())
harita_isle()
calis(3)
assert abs(arac.x - kx) < 0.5 and abs(arac.y - ky) < 0.5

print('\nGERI BILDIRIMLER:')
for d, m in fb:
    print(f'  {d:11} {m}')
print('\nTUM KONTROLLER GECTI')
