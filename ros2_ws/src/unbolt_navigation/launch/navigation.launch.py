"""Navigation on a saved map: MuJoCo sim + Nav2 (map_server, AMCL, planner, controller, BT navigator) + RViz.

  ros2 launch unbolt_navigation navigation.launch.py
  ros2 launch unbolt_navigation navigation.launch.py map:=/path/to/map.yaml

Set goals with the "2D Goal Pose" tool in RViz, or run:
  ros2 run unbolt_navigation nav_goal_test.py --ros-args -p use_sim_time:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav_share = FindPackageShare('unbolt_navigation')
    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz'),
        DeclareLaunchArgument('model_path', default_value='', description='MJCF scene (default: models/scene.xml)'),
        DeclareLaunchArgument('map', default_value=PathJoinSubstitution([nav_share, 'maps', 'unbolt_room.yaml'])),
        DeclareLaunchArgument('params_file', default_value=PathJoinSubstitution([nav_share, 'config', 'nav2_params.yaml'])),
        # Scoped so the include's rviz:=false does not overwrite this file's 'rviz' argument.
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('unbolt_mujoco_bridge'), 'launch', 'sim.launch.py']),
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'), 'rviz': 'false',
                              'model_path': LaunchConfiguration('model_path')}.items(),
        )]),
        IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'bringup_launch.py']),
            launch_arguments={
                'slam': 'False',
                'map': LaunchConfiguration('map'),
                'params_file': LaunchConfiguration('params_file'),
                'use_sim_time': 'True',
                'autostart': 'True',
            }.items(),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([nav_share, 'rviz', 'nav.rviz'])],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
