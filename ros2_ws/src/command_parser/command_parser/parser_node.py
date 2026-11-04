"""parser_node: /voice/text -> normalize -> acil -> hizli yol -> LLM -> /drone/command

Iki giris var, ayni hatta gider:
  /voice/text (String)    : terminal, telefon (yazili metin)
  /voice/stt  (VoiceText) : stt_node (Faz 3); zaman damgalari CommandList'e tasinir

    ros2 topic pub --once /voice/text std_msgs/msg/String \
        "{data: 'önce 20 metre yüksel sonra kuzeye 50 metre git'}"
"""
import threading

from drone_interfaces.msg import CommandList, DroneCommand, Feedback, VoiceText
import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String

from .fast_path import acil_mi
from .komut_cozucu import KomutCozucu
from .llm_client import LLMIstemcisi
from .normalize import normalize
from .prompt import KISA_SISTEM_PROMPT, SISTEM_PROMPT
from .schema import msg_alanlarina


def adim_to_msg(adim):
    msg = DroneCommand()
    for alan, deger in msg_alanlarina(adim).items():
        setattr(msg, alan, deger)
    return msg


class ParserNode(Node):

    def __init__(self):
        super().__init__('command_parser')
        p = self.declare_parameter
        llm_acik = p('llm_acik', True).value
        url = p('llm_url', 'http://127.0.0.1:8080').value
        kisa_prompt = p('kisa_prompt', False).value     # Faz 4: fine-tune'lu model
        llm = None
        if llm_acik:
            llm = LLMIstemcisi(
                url=url,
                model=p('llm_model', 'yerel').value,
                zaman_asimi=float(p('llm_zaman_asimi_s', 5.0).value),
                max_tokens=int(p('llm_max_tokens', 64).value),
                sistem_prompt=KISA_SISTEM_PROMPT if kisa_prompt else SISTEM_PROMPT,
            )
        self.llm = llm
        self.cozucu = KomutCozucu(
            llm=llm,
            hizli_yol=p('hizli_yol_acik', True).value,
            onbellek_boyutu=int(p('onbellek_boyutu', 256).value),
        )

        self.komut_pub = self.create_publisher(CommandList, '/drone/command', 10)
        self.feedback_pub = self.create_publisher(Feedback, '/drone/feedback', 10)

        # Acil yol LLM'i beklemesin: metin geri cagirimi tekrar girilebilir,
        # LLM cagrilari ise kilitle sirayla yapilir.
        self._kilit = threading.Lock()
        grup = ReentrantCallbackGroup()
        self.create_subscription(String, '/voice/text', self._metin_cb, 10, callback_group=grup)
        self.create_subscription(VoiceText, '/voice/stt', self._ses_cb, 10, callback_group=grup)

        if llm is not None:
            self._isinma_timer = self.create_timer(
                0.1, self._isit, callback_group=MutuallyExclusiveCallbackGroup())
        self.get_logger().info(f'Parser hazır (LLM: {url if llm else "kapalı"})')

    def _isit(self):
        self._isinma_timer.cancel()
        with self._kilit:
            if not self.llm.saglikli():
                self.get_logger().warn(
                    f'llama-server\'a ulaşılamadı ({self.llm.url}); yalnızca hızlı yol çalışır')
                return
            sonuc = self.llm.isit()
        if sonuc.basarili:
            self.get_logger().info(f'LLM ısınma isteği: {sonuc.sure_ms:.0f} ms')
        else:
            self.get_logger().warn(f'LLM ısınma başarısız: {sonuc.hata}')

    def _metin_cb(self, msg):
        self._isle(msg.data)

    def _ses_cb(self, msg):
        if not msg.metin.strip():
            return
        self._isle(msg.metin, msg)

    def _isle(self, ham, ses=None):
        t_metin = self.get_clock().now()
        # Acil kelimeler kilidi (LLM'i) beklemez.
        if acil_mi(normalize(ham)):
            cozum = self.cozucu.coz(ham)
        else:
            with self._kilit:
                cozum = self.cozucu.coz(ham)
        t_hazir = self.get_clock().now()

        if not cozum.komut_var:
            self.get_logger().info(
                f'"{ham}" -> komut yok [{cozum.kaynak}] {cozum.hata} ({cozum.sure_ms:.1f} ms)')
            self.feedback_pub.publish(Feedback(
                durum='reddedildi', mesaj=f'anlamadım: "{cozum.metin}" ({cozum.hata})'))
            return

        cikti = CommandList()
        if ses is not None:
            cikti.t_konusma_bitti = ses.t_konusma_bitti
            cikti.t_stt_bitti = ses.t_stt_bitti
            cikti.ses_kaynagi = ses.kaynak
        cikti.t_metin_geldi = t_metin.to_msg()
        cikti.t_komut_hazir = t_hazir.to_msg()
        cikti.adimlar = [adim_to_msg(a) for a in cozum.adimlar]
        cikti.kuyruga_ekle = cozum.kuyruga_ekle
        cikti.metin = cozum.metin
        cikti.kaynak = cozum.kaynak
        self.komut_pub.publish(cikti)

        llm = f', LLM {cozum.llm_ms:.0f} ms' if cozum.kaynak == 'llm' else ''
        self.get_logger().info(
            f'"{ham}" -> "{cozum.metin}" -> {cozum.adimlar} '
            f'[{cozum.kaynak}{", kuyruğa" if cozum.kuyruga_ekle else ""}] '
            f'{cozum.sure_ms:.1f} ms{llm}')


def main(args=None):
    rclpy.init(args=args)
    node = ParserNode()
    yurutucu = MultiThreadedExecutor(num_threads=3)
    yurutucu.add_node(node)
    try:
        yurutucu.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
