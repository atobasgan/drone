"""Faz 2: yalnizca command_parser (/voice/text -> /drone/command).

    ros2 launch drone_bringup parser.launch.py
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
        DeclareLaunchArgument('parser', default_value=os.path.join(config, 'parser.yaml')),
        Node(
            package='command_parser',
            executable='parser_node',
            name='command_parser',
            parameters=[LaunchConfiguration('parser')],
            output='screen',
            emulate_tty=True,
        ),
    ])
