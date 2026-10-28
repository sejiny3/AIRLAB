"""Start the MuJoCo simulation with the ROS 2 bridge.

  ros2 launch airlab_mujoco_bridge bridge.launch.py
  ros2 launch airlab_mujoco_bridge bridge.launch.py use_viewer:=false
  ros2 launch airlab_mujoco_bridge bridge.launch.py model_path:=/path/to/scene.xml

An empty model_path (the default, also what the higher-level launch files pass through)
means $AIRLAB_ROOT/models/scene.xml. Without AIRLAB_ROOT the repo root is found through
the --symlink-install link back into ros2_ws/src, then ~/airlab.
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _default_root():
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), *['..'] * 4))
    if os.path.isfile(os.path.join(root, 'models', 'scene.xml')):
        return root
    return os.path.expanduser('~/airlab')


AIRLAB_ROOT = os.environ.get('AIRLAB_ROOT') or _default_root()


def _bridge_node(context):
    model_path = LaunchConfiguration('model_path').perform(context) or os.path.join(AIRLAB_ROOT, 'models', 'scene.xml')
    return [Node(
        package='airlab_mujoco_bridge',
        executable='mujoco_bridge',
        name='mujoco_bridge',
        output='screen',
        parameters=[{
            'model_path': model_path,
            'use_viewer': LaunchConfiguration('use_viewer'),
            'real_time_factor': LaunchConfiguration('real_time_factor'),
            'lidar_samples': LaunchConfiguration('lidar_samples'),
            'camera_rate': float(LaunchConfiguration('camera_rate').perform(context)),
            'wrist_camera_rate': float(LaunchConfiguration('wrist_camera_rate').perform(context)),
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('model_path', default_value='', description='MJCF scene (default: models/scene.xml)'),
        DeclareLaunchArgument('use_viewer', default_value='true'),
        DeclareLaunchArgument('real_time_factor', default_value='1.0'),
        DeclareLaunchArgument('lidar_samples', default_value='360', description='LiDAR beams per turn'),
        DeclareLaunchArgument('camera_rate', default_value='5.0', description='head camera images per second'),
        DeclareLaunchArgument('wrist_camera_rate', default_value='0.0',
                              description='right wrist camera images per second (0 = off; the VLA policy uses 10)'),
        OpaqueFunction(function=_bridge_node),
    ])
