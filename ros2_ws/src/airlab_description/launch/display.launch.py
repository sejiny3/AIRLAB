"""Inspect the URDF without the simulator: robot_state_publisher + joint sliders + RViz.

  ros2 launch airlab_description display.launch.py
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare('airlab_description')
    return LaunchDescription([
        IncludeLaunchDescription(PathJoinSubstitution([share, 'launch', 'rsp.launch.py'])),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui'),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([share, 'rviz', 'airlab.rviz']), '-f', 'base_footprint'],
        ),
    ])
