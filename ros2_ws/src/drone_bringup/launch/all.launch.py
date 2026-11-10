"""Tum ROS 2 node'lari: yurutucu + parser + ses (stt_node) + latency_monitor.

PX4 SITL, MicroXRCEAgent ve llama-server ayri surecler olarak calisir
(scripts/hepsini_baslat.sh).

    ros2 launch drone_bringup all.launch.py                    # mikrofonla
    ros2 launch drone_bringup all.launch.py stt_mod:=ikisi     # + kayitli WAV testi
    ros2 launch drone_bringup all.launch.py ses_acik:=false    # Faz 2 gibi (yalnizca metin)
    ros2 launch drone_bringup all.launch.py ft:=true           # Faz 4 fine-tune'lu model
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    launch_dir = os.path.join(get_package_share_directory('drone_bringup'), 'launch')

    def dahil(ad, kosul=None, **arg):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, ad)),
            launch_arguments=arg.items(), condition=kosul)

    return LaunchDescription([
        DeclareLaunchArgument('ses_acik', default_value='true'),
        DeclareLaunchArgument('stt_mod', default_value='mikrofon', description='mikrofon | dosya | ikisi'),
        DeclareLaunchArgument('ft', default_value='false', description='Faz 4 fine-tune\'lu model'),
        dahil('executor.launch.py'),
        dahil('parser.launch.py', ft=LaunchConfiguration('ft')),
        dahil('ses.launch.py', IfCondition(LaunchConfiguration('ses_acik')),
              mod=LaunchConfiguration('stt_mod')),
        dahil('gecikme.launch.py'),
    ])
