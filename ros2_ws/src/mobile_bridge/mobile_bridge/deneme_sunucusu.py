"""ROS ve PX4 OLMADAN telsiz uygulamasini denemek icin sunucu.

Telefon uygulamasi gercek kopruyle ayni protokolu konusur; bu sunucu ROS yerine:
  - metni GERCEK command_parser hattindan gecirir (normalize -> acil -> hizli yol
    -> istenirse llama-server LLM) ve uretilen JSON'u telefona gonderir,
  - komutu GERCEK mission_executor guvenlik katmaniyla, sanal bir drone uzerinde
    kontrol eder; "yurutuyor / tamamlandi / reddedildi" geri bildirimlerini ve
    sanal telemetriyi uretir.

    python3 -m mobile_bridge.deneme_sunucusu                      # sadece hizli yol
    python3 -m mobile_bridge.deneme_sunucusu --llm http://127.0.0.1:8080
    python3 -m mobile_bridge.deneme_sunucusu --stt faster_whisper # yer STT modu
    python3 -m mobile_bridge.deneme_sunucusu --sahte-stt "kalk"   # her sese "kalk" de

Telefonda terminaldeki QR kodu okut (telefon ve bilgisayar ayni Wi-Fi'da olmali).
"""
import argparse
import asyncio
import os
import secrets
import time

from command_parser.komut_cozucu import KomutCozucu
from command_parser.llm_client import LLMIstemcisi
from command_parser.schema import msg_alanlarina
from mission_executor import mesajlar
from mission_executor.planlayici import Poz
from mission_executor.safety import AracDurumu, Guvenlik, Limitler, Reddedildi

from . import protokol
from .cekirdek import Ayarlar, RosArayuzu, TelsizCekirdegi
from .qr_kod import terminale_yaz, yerel_ip
from .stt_motoru import STTMotoru, motor_olustur
from .sunucu import TelsizSunucusu

# Sanal drone hizlari (gorsel geri bildirim icin; gercek fizik degil)
YATAY_MPS, DIKEY_MPS, DONUS_DPS = 5.0, 3.0, 45.0


class SahteSTT(STTMotoru):
    ad = 'sahte'
    hazir = True

    def __init__(self, metin):
        self.metin = metin

    def yaziya_cevir(self, pcm, hz):
        return self.metin


class SanalDrone(RosArayuzu):
    """ROS'un yerine: parser + guvenlik + yurutme benzetimi."""

    def __init__(self, cozucu, stt, hiz_katsayisi=1.0):
        self.cozucu = cozucu
        self.stt = stt
        self.hiz_katsayisi = hiz_katsayisi
        self.guvenlik = Guvenlik(Limitler(max_irtifa=120.0))
        self.durum = AracDurumu(poz=Poz(), havada=False, batarya=1.0)
        self.sunucu = None
        self._gorev = None
        self.acil_nesli = 0

    # -- yardimci: cekirdek ciktisini gonder (dongu icinde)
    def _yolla(self, cikti):
        asyncio.ensure_future(self.sunucu._gonder(cikti))

    @property
    def cek(self):
        return self.sunucu.cekirdek

    def metin_yayinla(self, metin):
        # Parser (ozellikle LLM) olay dongusunu BLOKLAMAMALI: yoksa o sirada
        # gelen ACIL DUR beklerdi. Gercek koprude parser zaten ayri bir node.
        asyncio.ensure_future(self._isle(metin))

    async def _isle(self, metin):
        t0 = time.perf_counter()
        nesil = self.acil_nesli
        cozum = await asyncio.get_running_loop().run_in_executor(None, self.cozucu.coz, metin)
        print(f'  "{metin}" -> {cozum.adimlar or "komut yok"} [{cozum.kaynak}] {cozum.sure_ms:.1f} ms')
        if cozum.kaynak != 'acil' and nesil != self.acil_nesli:
            # parser_node ile ayni kural: cozulurken ACIL DUR geldiyse sonucu at
            self._yolla(self.cek.ros_geri_bildirim(
                'iptal', f'ACİL DUR geldiği için "{cozum.metin}" iptal edildi'))
            return
        if not cozum.komut_var:
            self._yolla(self.cek.ros_geri_bildirim(
                'reddedildi', f'anlamadım: "{cozum.metin}" ({cozum.hata})'))
            return
        self._yolla(self.cek.ros_komut({
            'metin': cozum.metin, 'kaynak': cozum.kaynak, 'kuyruga_ekle': cozum.kuyruga_ekle,
            'adimlar': cozum.adimlar, 'parser_ms': round((time.perf_counter() - t0) * 1000, 1)}))
        komutlar = [msg_alanlarina(a) for a in cozum.adimlar]
        if komutlar[0]['komut'] == 'dur':
            self.acil_dur_yayinla()
            self._yolla(self.cek.ros_geri_bildirim('tamamlandi', 'duruyorum'))
            return
        try:
            hedefler = self.guvenlik.liste_kontrol_et(komutlar, self.durum)
        except Reddedildi as e:
            self._yolla(self.cek.ros_geri_bildirim('reddedildi', str(e)))
            return
        if self._gorev and not cozum.kuyruga_ekle:
            self._gorev.cancel()
        self._gorev = asyncio.ensure_future(self._yurut(komutlar, hedefler))

    async def _yurut(self, komutlar, hedefler):
        self._yolla(self.cek.ros_geri_bildirim('kabul', f'{len(komutlar)} adım kabul edildi'))
        for komut, hedef in zip(komutlar, hedefler):
            self._yolla(self.cek.ros_geri_bildirim('yurutuyor', mesajlar.baslarken(komut)))
            await asyncio.sleep(self._sure(komut, hedef) / self.hiz_katsayisi)
            self.durum = Guvenlik.sonraki_durum(self.durum, hedef)
            self.durum = AracDurumu(poz=self.durum.poz, havada=self.durum.havada,
                                    batarya=max(0.0, self.durum.batarya - 0.01))
            self._yolla(self.cek.ros_geri_bildirim('tamamlandi', f'{komut["komut"]} tamamlandı'))

    def _sure(self, komut, hedef):
        a, b = self.durum.poz, hedef.poz
        if hedef.tip == 'bekle':
            return hedef.saniye
        yatay = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 / YATAY_MPS
        dikey = abs(a.z - b.z) / DIKEY_MPS
        donus = abs(a.yaw - b.yaw) * 57.3 / DONUS_DPS
        return min(max(yatay, dikey, donus, 0.5), 20.0)

    def acil_dur_yayinla(self):
        self.acil_nesli += 1
        if self._gorev:
            self._gorev.cancel()
            self._gorev = None
        print('  ACİL DUR')

    def stt_baslat(self, konusma):
        async def calistir():
            t0 = time.perf_counter()
            dongu = asyncio.get_running_loop()
            try:
                metin = await dongu.run_in_executor(None, self.stt.yaziya_cevir, konusma.pcm(),
                                                    protokol.ORNEKLEME_HZ)
                hata = None
            except Exception as e:
                metin, hata = '', f'STT hatası: {e}'
            sure = (time.perf_counter() - t0) * 1000
            print(f'  STT #{konusma.konusma_id}: "{metin}" ({sure:.0f} ms)')
            self._yolla(self.cek.stt_sonucu(konusma, metin, sure, hata))
        asyncio.ensure_future(calistir())

    def telemetri(self):
        p, d = self.durum.poz, self.durum
        return {'hazir': True, 'irtifa': round(p.irtifa, 1), 'hiz': 0.0,
                'yaw': round((p.yaw * 57.2958) % 360), 'x': round(p.x, 1), 'y': round(p.y, 1),
                'batarya': round(d.batarya, 2), 'arm': d.havada, 'havada': d.havada,
                'mod': 'OFFBOARD' if d.havada else 'BEKLE (HOLD)'}


async def calis(args, hazir=None):
    llm = None
    if args.llm:
        llm = LLMIstemcisi(url=args.llm)
        print('LLM:', args.llm, 'erişilebilir' if llm.saglikli() else 'ERİŞİLEMİYOR (sadece hızlı yol)')
    if args.sahte_stt is not None:
        stt = SahteSTT(args.sahte_stt)
    else:
        ayar = {'model': args.stt_model, 'hesaplama': args.stt_hesaplama} if args.stt != 'yok' else {}
        stt = motor_olustur(args.stt, **ayar)
    if llm is not None and llm.saglikli():
        print(f'LLM ısınma: {llm.isit().sure_ms:.0f} ms')
    if hasattr(stt, 'isit'):
        print(f'STT ısınma: {stt.isit():.0f} ms')
    drone = SanalDrone(KomutCozucu(llm=llm), stt, hiz_katsayisi=args.hiz)
    token = args.token or os.environ.get('TELSIZ_TOKEN') or secrets.token_urlsafe(9)
    cekirdek = TelsizCekirdegi(drone, Ayarlar(token=token, baglanti_koparsa='dur',
                                              kayit_klasoru=args.kayit or ''),
                               stt_hazir=stt.hazir, stt_adi=stt.ad)
    sunucu = TelsizSunucusu(cekirdek, args.host, args.port)
    drone.sunucu = sunucu
    gorev = asyncio.ensure_future(sunucu.calis())
    await sunucu.hazir_bekle()
    adres = protokol.baglanti_adresi(args.ilan_ip or yerel_ip(), sunucu.port, token)
    print(f'\nDeneme sunucusu (ROS yok). Telefonda okut:\n{adres}\n{terminale_yaz(adres)}')
    print(f'STT: {stt.ad} | LLM: {args.llm or "yok"} | Ctrl+C ile çık\n', flush=True)
    if hazir:
        hazir(sunucu, adres)

    async def telemetri_dongusu():
        while True:
            await asyncio.sleep(0.5)
            await sunucu._gonder(cekirdek.telemetri(drone.telemetri()))
    t = asyncio.ensure_future(telemetri_dongusu())
    await gorev
    t.cancel()


def arguman_cozucu():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--host', default='0.0.0.0')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--ilan-ip', default='', help='QR koda yazılacak IP (boş = otomatik)')
    ap.add_argument('--token', default='')
    ap.add_argument('--llm', default='', help='llama-server adresi, ör. http://127.0.0.1:8080')
    ap.add_argument('--stt', default='yok', choices=['yok', 'faster_whisper'])
    ap.add_argument('--stt-model', default='small')
    ap.add_argument('--stt-hesaplama', default='default', help='CPU: int8, GPU: float16')
    ap.add_argument('--sahte-stt', default=None, help='her ses için bu metni döndür (test)')
    ap.add_argument('--kayit', default='', help='konuşmaları WAV olarak bu klasöre kaydet')
    ap.add_argument('--hiz', type=float, default=1.0, help='sanal yürütme hız katsayısı')
    return ap


def main(argv=None):
    args = arguman_cozucu().parse_args(argv)
    try:
        asyncio.run(calis(args))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
