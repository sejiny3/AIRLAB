"""Full step-2 stack: MuJoCo bridge + robot_state_publisher + RViz, all on simulation time.

  ros2 launch unbolt_mujoco_bridge sim.launch.py
  ros2 launch unbolt_mujoco_bridge sim.launch.py rviz:=false use_viewer:=false
  ros2 launch unbolt_mujoco_bridge sim.launch.py model_path:=$UNBOLT_ROOT/models/my_scene.xml
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bridge_share = FindPackageShare('unbolt_mujoco_bridge')
    description_share = FindPackageShare('unbolt_description')

    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz'),
        DeclareLaunchArgument('model_path', default_value='', description='MJCF scene (default: models/scene.xml)'),
        DeclareLaunchArgument('lidar_samples', default_value='360', description='LiDAR beams per turn'),
        DeclareLaunchArgument('camera_rate', default_value='5.0', description='head camera images per second'),
        DeclareLaunchArgument('wrist_camera_rate', default_value='0.0', description='right wrist camera (0 = off)'),
        IncludeLaunchDescription(
            PathJoinSubstitution([bridge_share, 'launch', 'bridge.launch.py']),
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'),
                              'model_path': LaunchConfiguration('model_path'),
                              'lidar_samples': LaunchConfiguration('lidar_samples'),
                              'camera_rate': LaunchConfiguration('camera_rate'),
                              'wrist_camera_rate': LaunchConfiguration('wrist_camera_rate')}.items(),
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([description_share, 'launch', 'rsp.launch.py']),
            launch_arguments={'use_sim_time': 'true'}.items(),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([description_share, 'rviz', 'unbolt.rviz'])],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
