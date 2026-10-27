"""Automatic mapping: MuJoCo sim + slam_toolbox + Nav2 (no saved map) + frontier explorer + RViz.

  ros2 launch unbolt_navigation explore.launch.py
  ros2 launch unbolt_navigation explore.launch.py autostart:=false   # start with /explore/control

The robot starts with an empty map and drives itself to the frontiers (edges of the known
area) until none is left; the map is then saved to ~/maps/unbolt_explored_<date>_<time>.yaml.
  ros2 topic pub --once /explore/control std_msgs/msg/String "{data: stop}"   # or start / save
  ros2 topic echo /explore/status --field data
Use the saved map for navigation:
  ros2 launch unbolt_navigation navigation.launch.py map:=$HOME/maps/unbolt_explored_<...>.yaml
"""

import tempfile

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# m: the 0.60 x 0.54 m base turning in place sweeps a 0.40 m circle, plus a little room for
# path-following error. It also closes the 0.87 m gap between the supply table and the pillar;
# the 1.2 m doorway keeps a 0.32 m wide lane (0.48 left 0.1 m and the robot got shut in).
SWEEP_RADIUS = 0.44


def _nav2(context):
    """Nav2 on our parameters, made safe for turning on the spot anywhere.

    The explorer switches goals wherever the robot happens to be, and every new goal starts
    with a turn in place. With the rectangular footprint Nav2 lets the base centre come
    within 0.3 m of the pillar or a wall corner, closer than the corners sweep (0.40 m): the
    base jams, the wheels slip, odometry turns while the robot does not, and slam_toolbox
    (which starts every scan match from odometry) draws the room twice at an angle. A circle
    around the whole base keeps the centre far enough away; turning slower helps the scan
    matcher too. Task mode keeps the exact rectangle it needs to dock at the tables.

    What the base kept hitting was a 4 cm supply table leg missing from the costmaps. The
    main cause was in the simulator: the bridge cast its LiDAR with mj_multiRay, which skipped
    two of the table legs from most of the room (it now uses one mj_ray per beam). The rest
    keeps thin obstacles in the costmaps once seen: 720 beams (at 360 a 4 cm leg falls between
    two beams beyond about 2.3 m), no footprint clearing (it wipes the leg as soon as the
    robot's circle reaches it) and a global costmap that is a fixed 20 x 20 m window around
    the robot (sized to /map it resizes whenever the map grows, which wipes every obstacle
    marked so far). Turning ray clearing off as well let stale marks close the doorway."""
    turn = float(LaunchConfiguration('max_turn').perform(context))
    params = yaml.safe_load(open(LaunchConfiguration('params_file').perform(context)))
    follow = params['controller_server']['ros__parameters']['FollowPath']
    follow['rotate_to_heading_angular_vel'] = turn
    follow['desired_linear_vel'] = 0.25
    follow['use_cost_regulated_linear_velocity_scaling'] = True  # slow down next to obstacles
    smoother = params['velocity_smoother']['ros__parameters']
    smoother['max_velocity'][2], smoother['min_velocity'][2] = turn, -turn
    for name in ('local_costmap', 'global_costmap'):
        costmap = params[name][name]['ros__parameters']
        costmap.pop('footprint', None)
        costmap['robot_radius'] = SWEEP_RADIUS
        # the obstacle layer wipes whatever lies inside the footprint; with a wide circle that is
        # the leg the robot is about to hit
        costmap['obstacle_layer']['footprint_clearing_enabled'] = False
        costmap['inflation_layer'].update(inflation_radius=0.9, cost_scaling_factor=3.0)  # paths keep to the middle
    params['global_costmap']['global_costmap']['ros__parameters'].update(rolling_window=True, width=20, height=20)
    out = tempfile.NamedTemporaryFile('w', prefix='unbolt_explore_nav2_', suffix='.yaml', delete=False)
    yaml.safe_dump(params, out)
    out.close()
    # Nav2 without map_server/AMCL: slam_toolbox provides /map and map -> odom.
    return [IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'navigation_launch.py']),
        launch_arguments={'params_file': out.name, 'use_sim_time': 'True', 'autostart': 'True'}.items(),
    )]


def generate_launch_description():
    nav_share = FindPackageShare('unbolt_navigation')
    return LaunchDescription([
        DeclareLaunchArgument('use_viewer', default_value='true', description='open the MuJoCo viewer'),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz'),
        DeclareLaunchArgument('model_path', default_value='', description='MJCF scene (default: models/scene.xml)'),
        DeclareLaunchArgument('params_file', default_value=PathJoinSubstitution([nav_share, 'config', 'nav2_params.yaml'])),
        DeclareLaunchArgument('autostart', default_value='true', description='start exploring once Nav2 is up'),
        DeclareLaunchArgument('map_dir', default_value='~/maps', description='where the finished map is saved'),
        DeclareLaunchArgument('max_turn', default_value='0.5', description='rad/s; task mode turns at 0.8'),
        # Scoped so the include's rviz:=false does not overwrite this file's 'rviz' argument.
        GroupAction([IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('unbolt_mujoco_bridge'), 'launch', 'sim.launch.py']),
            # 720 beams (0.5 deg): at 360 a 4 cm table leg falls between beams beyond about 2.3 m, so
            # Nav2 learns about it only when the robot is already next to it
            launch_arguments={'use_viewer': LaunchConfiguration('use_viewer'), 'rviz': 'false',
                              'model_path': LaunchConfiguration('model_path'), 'lidar_samples': '720'}.items(),
        )]),
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[PathJoinSubstitution([nav_share, 'config', 'slam_toolbox.yaml']), {'use_sim_time': True}],
        ),
        OpaqueFunction(function=_nav2),
        Node(
            package='unbolt_navigation',
            executable='frontier_explorer.py',
            name='frontier_explorer',
            output='screen',
            parameters=[{'use_sim_time': True, 'autostart': LaunchConfiguration('autostart'),
                         'map_dir': LaunchConfiguration('map_dir')}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([nav_share, 'rviz', 'nav.rviz'])],
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
