"""Tum ROS 2 node'lari (Faz 2 itibariyla: yurutucu + parser).

PX4 SITL, MicroXRCEAgent ve llama-server ayri surecler olarak calisir
(scripts/hepsini_baslat.sh). Faz 3'te stt_node buraya eklenecek.

    ros2 launch drone_bringup all.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    launch_dir = os.path.join(get_package_share_directory('drone_bringup'), 'launch')

    def dahil(ad):
        return IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(launch_dir, ad)))

    return LaunchDescription([
        dahil('executor.launch.py'),
        dahil('parser.launch.py'),
    ])
