"""latency_monitor: /latency/olcum (LatencySample) -> CSV (Gorev 3.5)

    ros2 run latency_monitor monitor_node --ros-args -p klasor:=~/gecikme
    ros2 run latency_monitor ozet ~/gecikme/gecikme_<tarih>.csv
"""
import csv
import datetime
import os

from drone_interfaces.msg import LatencySample
import rclpy
from rclpy.node import Node

from .olcum import CSV_ALANLARI


def ns(t):
    return t.sec * 1_000_000_000 + t.nanosec


def ms(a, b):
    return f'{(b - a) / 1e6:.0f}' if a and b and b >= a else '-'


class MonitorNode(Node):

    def __init__(self):
        super().__init__('latency_monitor')
        klasor = os.path.expanduser(self.declare_parameter('klasor', '~/llm_drone_gecikme').value)
        os.makedirs(klasor, exist_ok=True)
        ad = datetime.datetime.now().strftime('gecikme_%Y%m%d_%H%M%S.csv')
        self.yol = os.path.join(klasor, ad)
        self._dosya = open(self.yol, 'w', encoding='utf-8', newline='')
        self._yazici = csv.DictWriter(self._dosya, fieldnames=CSV_ALANLARI)
        self._yazici.writeheader()
        self._dosya.flush()
        self.create_subscription(LatencySample, '/latency/olcum', self._cb, 50)
        self.get_logger().info(f'Gecikmeler yazılıyor: {self.yol}')

    def _cb(self, m):
        t = dict(zip(('t0', 't1', 'tm', 't2', 't3', 't4', 't5'), map(ns, (
            m.t0_konusma_bitti, m.t1_stt_bitti, m.t_metin_geldi, m.t2_komut_hazir,
            m.t3_yurutucu_aldi, m.t4_ilk_setpoint, m.t5_hiz_degisti))))
        self._yazici.writerow({
            'zaman': datetime.datetime.now().isoformat(timespec='milliseconds'),
            'metin': m.metin, 'kaynak': m.kaynak, 'ses_kaynagi': m.ses_kaynagi,
            'sonuc': m.sonuc, **t,
        })
        self._dosya.flush()
        self.get_logger().info(
            f'"{m.metin}" [{m.kaynak}, {m.sonuc}] STT {ms(t["t0"], t["t1"])} | '
            f'parser {ms(t["tm"], t["t2"])} | ROS {ms(t["t2"], t["t3"])} | '
            f'setpoint {ms(t["t3"], t["t4"])} | PX4 {ms(t["t4"], t["t5"])} | '
            f'TOPLAM {ms(t["t0"], t["t5"])} ms')

    def destroy_node(self):
        self._dosya.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
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
