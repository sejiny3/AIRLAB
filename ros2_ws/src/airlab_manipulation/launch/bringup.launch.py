"""Everything for mobile manipulation: MuJoCo sim + Nav2 (saved map) + move_group + ArUco detector.

  ros2 launch airlab_manipulation bringup.launch.py
  ros2 launch airlab_manipulation bringup.launch.py use_viewer:=false rviz:=false
  # then:
  ros2 run airlab_manipulation pick_place_demo --ros-args -p use_sim_time:=true

With the LLM task planner (needs ANTHROPIC_API_KEY in the environment):
  ros2 launch airlab_manipulation bringup.launch.py planner:=true
  ros2 run airlab_manipulation ask "빨간 상자를 작업대로 옮겨줘"

Everything, with the web dashboard at http://localhost:8080/:
  ros2 launch airlab_manipulation bringup.launch.py planner:=true dashboard:=true

Picking with the learned VLA policy instead of MoveIt (airlab_vla; train it first, see workshop/05_vla.md):
  ros2 launch airlab_manipulation bringup.launch.py planner:=true pick:=vla

On a map made by automatic exploration (airlab_dashboard mapping.launch.py):
  ros2 launch airlab_manipulation bringup.launch.py map:=$HOME/maps/airlab_explored_<...>.yaml
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    vla = PythonExpression(["'", LaunchConfiguration('pick'), "' == 'vla'"])
    # the policy runs at 10 Hz and was trained with a fresh head and wrist image every step
    camera_rate = PythonExpression(["'10.0' if '", LaunchConfiguration('pick'), "' == 'vla' else '5.0'"])
    wrist_rate = PythonExpression(["'10.0' if '", LaunchConfiguration('pick'), "' == 'vla' else '0.0'"])
    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz (navigation view)'),
        DeclareLaunchArgument('planner', default_value='false', description='start the LLM task planner'),
        DeclareLaunchArgument('llm', default_value='claude', description="planner backend: 'claude' or 'scripted'"),
        DeclareLaunchArgument('pick', default_value='classical',
                              description="'classical' (MoveIt from the marker pose) or 'vla' (learned policy)"),
        DeclareLaunchArgument('dashboard', default_value='false', description='start rosbridge + web dashboard (:8080)'),
        DeclareLaunchArgument('map', default_value=PathJoinSubstitution(
            [FindPackageShare('airlab_navigation'), 'maps', 'airlab_room.yaml']), description='Nav2 map (yaml)'),
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('airlab_dashboard'), 'launch', 'dashboard.launch.py']),
            launch_arguments={'map_yaml': LaunchConfiguration('map')}.items(),
        )], condition=IfCondition(LaunchConfiguration('dashboard'))),
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('airlab_navigation'), 'launch', 'navigation.launch.py']),
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'), 'rviz': LaunchConfiguration('rviz'),
                              'map': LaunchConfiguration('map'),
                              'camera_rate': camera_rate, 'wrist_camera_rate': wrist_rate}.items(),
        )]),
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('airlab_moveit_config'), 'launch', 'move_group.launch.py']),
            launch_arguments={'rviz': 'false'}.items(),
        )]),
        Node(
            package='airlab_manipulation',
            executable='aruco_detector',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
        Node(
            package='airlab_manipulation',
            executable='task_planner',
            output='screen',
            parameters=[{'use_sim_time': True, 'llm': LaunchConfiguration('llm'),
                         'pick_mode': LaunchConfiguration('pick')}],
            condition=IfCondition(LaunchConfiguration('planner')),
        ),
        Node(
            package='airlab_vla',
            executable='vla_pick',
            output='screen',
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(vla),
        ),
    ])
