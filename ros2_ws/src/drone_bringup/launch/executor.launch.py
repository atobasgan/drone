"""Faz 1: yalnizca gorev yurutucu (terminalden CommandList ile surulur).

    ros2 launch drone_bringup executor.launch.py
    ros2 launch drone_bringup executor.launch.py guvenlik:=/yol/benim.yaml
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
        DeclareLaunchArgument('guvenlik', default_value=os.path.join(config, 'guvenlik.yaml')),
        Node(
            package='mission_executor',
            executable='executor_node',
            name='mission_executor',
            parameters=[LaunchConfiguration('guvenlik')],
            output='screen',
            emulate_tty=True,
        ),
    ])
