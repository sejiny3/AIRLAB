"""Mapping: MuJoCo sim + slam_toolbox (online async) + RViz.

  ros2 launch airlab_navigation slam.launch.py
  # drive with teleop_twist_keyboard, or run the scripted tour:
  ros2 run airlab_navigation explore_waypoints.py --ros-args -p use_sim_time:=true
  # save the map:
  ros2 run nav2_map_server map_saver_cli -f <dir>/airlab_room --ros-args -p use_sim_time:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav_share = FindPackageShare('airlab_navigation')
    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz'),
        DeclareLaunchArgument('model_path', default_value='', description='MJCF scene (default: models/scene.xml)'),
        # Scoped so the include's rviz:=false does not overwrite this file's 'rviz' argument.
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('airlab_mujoco_bridge'), 'launch', 'sim.launch.py']),
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'), 'rviz': 'false',
                              'model_path': LaunchConfiguration('model_path')}.items(),
        )]),
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[PathJoinSubstitution([nav_share, 'config', 'slam_toolbox.yaml']), {'use_sim_time': True}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([nav_share, 'rviz', 'nav.rviz'])],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
