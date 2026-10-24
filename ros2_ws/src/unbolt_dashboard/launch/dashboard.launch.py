"""rosbridge websocket + the dashboard web server. Open http://localhost:8080/ in a browser.

  ros2 launch unbolt_dashboard dashboard.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('port', default_value='8080', description='dashboard HTTP port'),
        DeclareLaunchArgument('rosbridge_port', default_value='9090', description='rosbridge websocket port'),
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{'port': LaunchConfiguration('rosbridge_port'), 'use_sim_time': True}],
        ),
        Node(
            package='unbolt_dashboard',
            executable='dashboard_server',
            output='screen',
            parameters=[{'port': LaunchConfiguration('port'), 'rosbridge_port': LaunchConfiguration('rosbridge_port')}],
        ),
    ])
