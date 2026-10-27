"""rosbridge websocket + the dashboard web server. Open http://localhost:8080/ in a browser.

  ros2 launch unbolt_dashboard dashboard.launch.py

The page's "시스템 종료" button makes dashboard_server exit cleanly (code 0); that exit shuts
down the whole launch this file is part of (e.g. bringup.launch.py: simulator, Nav2, MoveIt,
planner, RViz). A crash of the server (non-zero code) does not.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, LogInfo, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _on_server_exit(event, _context):
    if event.returncode != 0:
        return None
    return [LogInfo(msg='dashboard requested shutdown: stopping all programs'),
            EmitEvent(event=Shutdown(reason='shutdown button on the dashboard'))]


def generate_launch_description():
    server = Node(
        package='unbolt_dashboard',
        executable='dashboard_server',
        output='screen',
        parameters=[{'port': LaunchConfiguration('port'), 'rosbridge_port': LaunchConfiguration('rosbridge_port'),
                     'map_yaml': LaunchConfiguration('map_yaml')}],
    )
    return LaunchDescription([
        DeclareLaunchArgument('port', default_value='8080', description='dashboard HTTP port'),
        DeclareLaunchArgument('rosbridge_port', default_value='9090', description='rosbridge websocket port'),
        DeclareLaunchArgument('map_yaml', default_value='', description='map drawn on the page (default: unbolt_room)'),
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{'port': LaunchConfiguration('rosbridge_port'), 'use_sim_time': True}],
        ),
        server,
        RegisterEventHandler(OnProcessExit(target_action=server, on_exit=_on_server_exit)),
    ])
