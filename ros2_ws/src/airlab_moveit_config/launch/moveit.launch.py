"""MuJoCo sim + MoveIt 2 move_group + RViz (MotionPlanning panel).

  ros2 launch airlab_moveit_config moveit.launch.py
  ros2 launch airlab_moveit_config moveit.launch.py use_viewer:=false rviz:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz with the MotionPlanning panel'),
        # Scoped so the include's rviz:=false does not overwrite this file's 'rviz' argument.
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('airlab_mujoco_bridge'), 'launch', 'sim.launch.py']),
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'), 'rviz': 'false'}.items(),
        )]),
        IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('airlab_moveit_config'), 'launch', 'move_group.launch.py']),
            launch_arguments={'rviz': LaunchConfiguration('rviz')}.items(),
        ),
    ])
