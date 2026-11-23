"""harita_parser_node: parser_node + Faz 5 harita komutlari (yere_git, "en yakın X'e git" hizli yolu).

    ros2 run command_parser harita_parser_node --ros-args --params-file parser.yaml

ParserNode'un TAMAMI aynen calisir (parametreler, topic'ler, isinma, acil nesli...);
yalnizca LLM istemcisi ve komut cozucu harita surumleriyle degistirilir.
"""
import rclpy
from rclpy.executors import MultiThreadedExecutor

from .harita_komutlari import HaritaKomutCozucu, HaritaLLMIstemcisi
from .parser_node import ParserNode


class HaritaParserNode(ParserNode):

    def __init__(self):
        super().__init__()
        eski = self.llm
        if eski is not None:
            self.llm = HaritaLLMIstemcisi(url=eski.url, model=eski.model, zaman_asimi=eski.zaman_asimi,
                                          max_tokens=eski.max_tokens, sistem_prompt=eski.sistem_prompt)
        self.cozucu = HaritaKomutCozucu(llm=self.llm, hizli_yol=self.cozucu.hizli_yol,
                                        onbellek_boyutu=self.cozucu.onbellek_boyutu)
        self.get_logger().info('harita komutları açık: yakin_yere_git hızlı yolu, yere_git')


def main(args=None):
    rclpy.init(args=args)
    node = HaritaParserNode()
    yurutucu = MultiThreadedExecutor(num_threads=3)      # parser_node.main ile ayni
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
