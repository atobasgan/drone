"""stt_node: mikrofon / WAV -> VAD -> STT -> /voice/stt (Gorev 3.3)

Modlar ('mod' parametresi):
  mikrofon : sounddevice ile 16 kHz akis; Silero VAD konusmayi ayirir
  dosya    : /voice/dosya'ya (String) WAV yolu gelince dosyanin tamami STT'ye
             verilir. Kayitli test seti (ses_testi) bunu kullanir.
  ikisi    : ikisi birden
Yayin: /voice/stt (VoiceText) -> command_parser. t0 = konusma bitti (VAD;
dosya modunda dosya alindi), t1 = STT bitti.

    ros2 run voice_input stt_node --ros-args -p mod:=mikrofon
    ros2 topic echo /voice/stt

Uc thread: ses geri cagirimi -> VAD -> STT. VAD, STT'yi beklemez; boylece
STT calisirken biten bir sonraki konusmanin t0'i dogru olur.
"""
import datetime
import os
import queue
import threading

from drone_interfaces.msg import VoiceText
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .stt import DRONE_SOZLUGU, FasterWhisperSTT, STTSonucu
from .vad import CERCEVE, HZ, KonusmaAyirici, SileroVAD
from .wav import wav_oku, wav_yaz


def cihaz_sec(deger):
    """'' -> varsayilan, '3' -> 3 numarali cihaz, 'USB' -> adinda USB gecen cihaz."""
    deger = str(deger).strip()
    if not deger:
        return None
    return int(deger) if deger.isdigit() else deger


class STTNode(Node):

    def __init__(self):
        super().__init__('stt_node')

        def p(ad, varsayilan):
            return self.declare_parameter(ad, varsayilan).value

        self.mod = p('mod', 'mikrofon')
        if self.mod not in ('mikrofon', 'dosya', 'ikisi'):
            raise ValueError(f'mod mikrofon|dosya|ikisi olmalı: {self.mod}')
        self.kayit_klasoru = os.path.expanduser(p('kayit_klasoru', ''))

        self.pub = self.create_publisher(VoiceText, '/voice/stt', 10)
        self._stt_kuyruk = queue.Queue()

        self.get_logger().info('STT modeli yükleniyor (ilk seferde indirilir)...')
        self.stt = FasterWhisperSTT(
            model=p('stt_model', 'small'),
            cihaz=p('stt_cihaz', 'auto'),
            hesaplama=p('stt_hesaplama', 'int8'),
            beam_size=int(p('stt_beam', 1)),
            ilk_prompt=p('ilk_prompt', DRONE_SOZLUGU),
            thread=int(p('stt_thread', 0)),
        )
        self.get_logger().info(f'STT hazır: {self.stt.ad}, ısınma {self.stt.isit():.0f} ms')
        threading.Thread(target=self._stt_dongusu, daemon=True).start()

        if self.mod in ('dosya', 'ikisi'):
            self.create_subscription(String, '/voice/dosya', self._dosya_cb, 10)
            self.get_logger().info('Dosya modu: /voice/dosya dinleniyor')

        if self.mod in ('mikrofon', 'ikisi'):
            self.ayirici = KonusmaAyirici(
                SileroVAD(),
                esik=float(p('vad_esik', 0.5)),
                bitis_sessizlik_ms=float(p('bitis_sessizlik_ms', 400.0)),
                on_kayit_ms=float(p('on_kayit_ms', 200.0)),
                min_konusma_ms=float(p('min_konusma_ms', 250.0)),
                max_konusma_s=float(p('max_konusma_s', 10.0)),
            )
            self._mikrofonu_ac(cihaz_sec(p('mikrofon_cihazi', '')))

    # ------------------------------------------------------------- mikrofon
    def _mikrofonu_ac(self, cihaz):
        import sounddevice as sd
        self._ses_kuyruk = queue.Queue()
        self._tasma = 0

        def geri_cagirim(veri, _kare, _zaman, durum):
            if durum.input_overflow:
                self._tasma += 1
            self._ses_kuyruk.put(veri[:, 0].copy())

        self._akis = sd.InputStream(samplerate=HZ, channels=1, dtype='float32',
                                    blocksize=CERCEVE, device=cihaz, callback=geri_cagirim)
        self._akis.start()
        threading.Thread(target=self._vad_dongusu, daemon=True).start()
        ad = sd.query_devices(self._akis.device)['name']
        self.get_logger().info(f'Mikrofon açık: {ad} ({HZ} Hz)')

    def _vad_dongusu(self):
        while rclpy.ok():
            parca = self._ses_kuyruk.get()
            for konusma in self.ayirici.besle(parca):
                t0 = self.get_clock().now()
                self._stt_kuyruk.put(('mikrofon', konusma.ornekler, t0, ''))
            if self._tasma:
                self.get_logger().warn(f'mikrofon tamponu taştı ({self._tasma} kez); CPU yetişmiyor')
                self._tasma = 0

    # ------------------------------------------------------------- dosya
    def _dosya_cb(self, msg):
        t0 = self.get_clock().now()
        yol = os.path.expanduser(msg.data.strip())
        try:
            ornekler = wav_oku(yol)
        except (OSError, ValueError, EOFError) as e:
            self.get_logger().error(f'WAV okunamadı: {yol}: {e}')
            ornekler = np.zeros(0, np.float32)
        self._stt_kuyruk.put(('dosya', ornekler, t0, msg.data))

    # ------------------------------------------------------------- STT
    def _stt_dongusu(self):
        while rclpy.ok():
            kaynak, ornekler, t0, dosya = self._stt_kuyruk.get()
            if len(ornekler):
                sonuc = self.stt.cevir(ornekler)
            else:
                sonuc = STTSonucu('', 0.0, 'boş ses')
            t1 = self.get_clock().now()
            sure_s = len(ornekler) / HZ

            if kaynak == 'mikrofon' and not sonuc.metin:
                self.get_logger().info(f'konuşma değil, atıldı ({sure_s:.1f} sn) {sonuc.atilan}')
                continue
            self.pub.publish(VoiceText(
                metin=sonuc.metin, kaynak=kaynak, dosya=dosya,
                t_konusma_bitti=t0.to_msg(), t_stt_bitti=t1.to_msg(), konusma_s=sure_s))
            self.get_logger().info(
                f'[{kaynak}] "{sonuc.metin}" ({sure_s:.1f} sn ses, STT {sonuc.sure_ms:.0f} ms)')
            if kaynak == 'mikrofon' and self.kayit_klasoru:
                self._kaydet(ornekler, sonuc.metin)

    def _kaydet(self, ornekler, metin):
        """Faz 4 icin gercek veri: her konusmayi WAV + duyulan metin olarak saklar."""
        os.makedirs(self.kayit_klasoru, exist_ok=True)
        ad = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        wav_yaz(os.path.join(self.kayit_klasoru, ad + '.wav'), ornekler)
        with open(os.path.join(self.kayit_klasoru, 'duyulanlar.tsv'), 'a', encoding='utf-8') as f:
            f.write(f'{ad}.wav\t{metin}\n')


def main(args=None):
    rclpy.init(args=args)
    node = STTNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
