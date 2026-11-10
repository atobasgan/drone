"""Faz 2: yalnizca command_parser (/voice/text -> /drone/command).

    ros2 launch drone_bringup parser.launch.py
    ros2 launch drone_bringup parser.launch.py ft:=true    # Faz 4: fine-tune'lu model, kisa prompt
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(get_package_share_directory('drone_bringup'), 'config')
    ft = LaunchConfiguration('ft')

    def parser_node(ayar, kosul):
        return Node(package='command_parser', executable='parser_node', name='command_parser',
                    parameters=[ayar], output='screen', emulate_tty=True, condition=kosul)

    return LaunchDescription([
        DeclareLaunchArgument('parser', default_value=os.path.join(config, 'parser.yaml')),
        DeclareLaunchArgument('ft', default_value='false',
                              description='true: fine-tune\'lu model (parser_ft.yaml, kisa prompt)'),
        parser_node(LaunchConfiguration('parser'), UnlessCondition(ft)),
        parser_node(os.path.join(config, 'parser_ft.yaml'), IfCondition(ft)),
    ])
