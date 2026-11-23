"""Faz 5: harita komutlari ile tum sistem.

    parser ─/drone/command─> harita_node ─/drone/command_harita─> mission_executor

Yurutucu ayni executor.launch.py ile baslar; yalnizca girisi SetRemap ile
/drone/command_harita'ya yonlendirilir (yurutucu kodu degismez).

    ros2 launch drone_bringup harita.launch.py
    ros2 launch drone_bringup harita.launch.py ft:=true ses_acik:=false
    ros2 launch drone_bringup harita.launch.py harita:=/yol/benim_harita.yaml
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap


def generate_launch_description():
    paylasim = get_package_share_directory('drone_bringup')
    launch_dir = os.path.join(paylasim, 'launch')
    config = os.path.join(paylasim, 'config')
    ft = LaunchConfiguration('ft')
    harita = LaunchConfiguration('harita')

    def dahil(ad, kosul=None, **arg):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(launch_dir, ad)),
            launch_arguments=arg.items(), condition=kosul)

    def dugum(paket, calistirilabilir, ad, ayar, kosul=None):
        return Node(package=paket, executable=calistirilabilir, name=ad, parameters=[ayar],
                    output='screen', emulate_tty=True, condition=kosul)

    return LaunchDescription([
        DeclareLaunchArgument('ses_acik', default_value='true'),
        DeclareLaunchArgument('stt_mod', default_value='mikrofon', description='mikrofon | dosya | ikisi'),
        DeclareLaunchArgument('ft', default_value='false', description='Faz 4 fine-tune\'lu model'),
        DeclareLaunchArgument('harita', default_value=os.path.join(config, 'harita.yaml')),

        # yurutucu: /drone/command yerine harita_node'un cikisini dinler
        GroupAction([SetRemap(src='/drone/command', dst='/drone/command_harita'),
                     dahil('executor.launch.py')]),

        # parser: yere_git'i de taniyan alt sinif (ayni parser.yaml / parser_ft.yaml)
        dugum('command_parser', 'harita_parser_node', 'command_parser',
              os.path.join(config, 'parser.yaml'), UnlessCondition(ft)),
        dugum('command_parser', 'harita_parser_node', 'command_parser',
              os.path.join(config, 'parser_ft.yaml'), IfCondition(ft)),

        dugum('map_tools', 'harita_node', 'harita_node', harita),
        dugum('map_tools', 'places_node', 'places_node', harita),

        dahil('ses.launch.py', IfCondition(LaunchConfiguration('ses_acik')),
              mod=LaunchConfiguration('stt_mod')),
        dahil('gecikme.launch.py'),
    ])
