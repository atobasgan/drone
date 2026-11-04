"""Gorev 3.2 / 3.4: yurutucusuz dogruluk testi (drone ucmaz).

stt_node dosya modunda + parser + latency_monitor. Sonra:
    ros2 run voice_input ses_testi --etiket "small int8 + qwen3-1.7b"
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    launch_dir = os.path.join(get_package_share_directory('drone_bringup'), 'launch')

    def dahil(ad, **arg):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, ad)),
            launch_arguments=arg.items())

    return LaunchDescription([
        dahil('ses.launch.py', mod='dosya'),
        dahil('parser.launch.py'),
        dahil('gecikme.launch.py'),
    ])
