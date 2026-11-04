"""Faz 3: latency_monitor (/latency/olcum -> CSV).

    ros2 launch drone_bringup gecikme.launch.py klasor:=~/gecikme
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('klasor', default_value='~/llm_drone_gecikme'),
        Node(
            package='latency_monitor',
            executable='monitor_node',
            name='latency_monitor',
            parameters=[{'klasor': LaunchConfiguration('klasor')}],
            output='screen',
            emulate_tty=True,
        ),
    ])
