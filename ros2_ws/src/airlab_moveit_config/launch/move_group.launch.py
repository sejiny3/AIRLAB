"""move_group (+ optional RViz MotionPlanning) on sim time, without starting the simulator.

Included by moveit.launch.py and by airlab_manipulation's bringup.launch.py.
"""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def airlab_moveit_config():
    xacro_file = get_package_share_directory('airlab_description') + '/urdf/airlab.urdf.xacro'
    return (
        MoveItConfigsBuilder('airlab', package_name='airlab_moveit_config')
        .robot_description(file_path=xacro_file)
        .robot_description_semantic(file_path='config/airlab.srdf')
        .robot_description_kinematics(file_path='config/kinematics.yaml')
        .joint_limits(file_path='config/joint_limits.yaml')
        .trajectory_execution(file_path='config/moveit_controllers.yaml')
        .planning_pipelines(pipelines=['ompl'])
        .to_moveit_configs()
    )


def generate_launch_description():
    moveit_config = airlab_moveit_config()
    sim_time = {'use_sim_time': True}
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='false', description='open RViz with the MotionPlanning panel'),
        Node(
            package='moveit_ros_move_group',
            executable='move_group',
            output='screen',
            parameters=[moveit_config.to_dict(), sim_time, {'publish_robot_description_semantic': True}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([FindPackageShare('airlab_moveit_config'), 'config', 'moveit.rviz'])],
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.planning_pipelines,
                moveit_config.joint_limits,
                sim_time,
            ],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
