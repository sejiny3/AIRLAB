"""Automatic mapping with the web dashboard: explore.launch.py (sim + SLAM + Nav2 + frontier
explorer) + rosbridge + dashboard_server. Open http://localhost:8080/ in a browser.

  ros2 launch unbolt_dashboard mapping.launch.py
  ros2 launch unbolt_dashboard mapping.launch.py use_viewer:=false rviz:=true

The page shows the map as slam_toolbox builds it, the frontiers and the explorer's goal, and
offers start/stop/save; once exploration is over the robot can be driven with the keyboard.
dashboard_launcher starts this file for its "지도 만들기" mode.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='false', description='open RViz'),
        DeclareLaunchArgument('autostart', default_value='true', description='start exploring once Nav2 is up'),
        DeclareLaunchArgument('map_dir', default_value='~/maps', description='where the finished map is saved'),
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('unbolt_dashboard'), 'launch', 'dashboard.launch.py']),
        )]),
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('unbolt_navigation'), 'launch', 'explore.launch.py']),
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'), 'rviz': LaunchConfiguration('rviz'),
                              'autostart': LaunchConfiguration('autostart'),
                              'map_dir': LaunchConfiguration('map_dir')}.items(),
        )]),
    ])
