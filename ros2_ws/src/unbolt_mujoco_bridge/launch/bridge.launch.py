"""Start the MuJoCo simulation with the ROS 2 bridge.

  ros2 launch unbolt_mujoco_bridge bridge.launch.py
  ros2 launch unbolt_mujoco_bridge bridge.launch.py use_viewer:=false
  ros2 launch unbolt_mujoco_bridge bridge.launch.py model_path:=/path/to/scene.xml

An empty model_path (the default, also what the higher-level launch files pass through)
means $UNBOLT_ROOT/models/scene.xml. Without UNBOLT_ROOT the repo root is found through
the --symlink-install link back into ros2_ws/src, then ~/unbolt.
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
    return os.path.expanduser('~/unbolt')


UNBOLT_ROOT = os.environ.get('UNBOLT_ROOT') or _default_root()


def _bridge_node(context):
    model_path = LaunchConfiguration('model_path').perform(context) or os.path.join(UNBOLT_ROOT, 'models', 'scene.xml')
    return [Node(
        package='unbolt_mujoco_bridge',
        executable='mujoco_bridge',
        name='mujoco_bridge',
        output='screen',
        parameters=[{
            'model_path': model_path,
            'use_viewer': LaunchConfiguration('use_viewer'),
            'real_time_factor': LaunchConfiguration('real_time_factor'),
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('model_path', default_value='', description='MJCF scene (default: models/scene.xml)'),
        DeclareLaunchArgument('use_viewer', default_value='true'),
        DeclareLaunchArgument('real_time_factor', default_value='1.0'),
        OpaqueFunction(function=_bridge_node),
    ])
