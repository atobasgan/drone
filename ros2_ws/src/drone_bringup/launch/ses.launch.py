"""Faz 3: stt_node (mikrofon / WAV -> /voice/stt).

    ros2 launch drone_bringup ses.launch.py
    ros2 launch drone_bringup ses.launch.py mod:=dosya
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(get_package_share_directory('drone_bringup'), 'config')
    return LaunchDescription([
        DeclareLaunchArgument('ses', default_value=os.path.join(config, 'ses.yaml')),
        DeclareLaunchArgument('mod', default_value='mikrofon', description='mikrofon | dosya | ikisi'),
        Node(
            package='voice_input',
            executable='stt_node',
            name='stt_node',
            parameters=[LaunchConfiguration('ses'), {'mod': LaunchConfiguration('mod')}],
            output='screen',
            emulate_tty=True,
        ),
    ])
