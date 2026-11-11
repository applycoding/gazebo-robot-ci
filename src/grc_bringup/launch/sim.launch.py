# SPDX-License-Identifier: Apache-2.0

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _world_name_from_path(world_path: str) -> str:
    base = os.path.basename(world_path)
    if base == 'stop_obstacle.sdf':
        return 'stop_obstacle'
    return 'reach_goal'


def _contact_bridges(context, *args, **kwargs):
    world_path = LaunchConfiguration('world').perform(context)
    world_name = _world_name_from_path(world_path)
    bringup_share = get_package_share_directory('grc_bringup')
    contact_cfg = os.path.join(
        bringup_share, 'config', f'bridge_contacts_{world_name}.yaml')
    relay_sources = ['/contacts_wheel']
    if world_name == 'stop_obstacle':
        relay_sources.append('/contacts_body')
    return [
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge_contacts',
            arguments=[
                '--ros-args',
                '-p', f'config_file:={contact_cfg}',
            ],
            output='screen',
        ),
        Node(
            package='grc_bringup',
            executable='contact_relay.py',
            name='grc_contact_relay',
            arguments=['--sources', *relay_sources],
            output='screen',
        ),
    ]


def generate_launch_description():
    bringup_share = get_package_share_directory('grc_bringup')
    robot_share = get_package_share_directory('grc_robot')
    models_path = os.path.join(robot_share, 'models')

    world_arg = DeclareLaunchArgument(
        'world', default_value=os.path.join(bringup_share, 'worlds', 'reach_goal.sdf'))
    start_follower_arg = DeclareLaunchArgument('start_follower', default_value='true')
    safety_enable_arg = DeclareLaunchArgument('safety_stop_enable', default_value='true')
    goal_bypass_arg = DeclareLaunchArgument('goal_safety_bypass', default_value='false')
    latch_release_arg = DeclareLaunchArgument('latch_release_enable', default_value='true')

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            )
        ]),
        launch_arguments={
            'gz_args': ['-s -r ', LaunchConfiguration('world')],
        }.items(),
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge_core',
        arguments=[
            '--ros-args',
            '-p', 'config_file:=' + os.path.join(bringup_share, 'config', 'bridge.yaml'),
        ],
        output='screen',
    )

    goal_x_arg = DeclareLaunchArgument('goal_x', default_value='4.0')
    goal_y_arg = DeclareLaunchArgument('goal_y', default_value='0.0')

    gz_plugins = os.pathsep.join(
        p for p in (
            '/opt/ros/lyrical/lib',
            '/opt/ros/lyrical/opt/gz_sim_vendor/lib',
            '/opt/ros/lyrical/opt/gz_plugins_vendor/lib',
            '/opt/ros/lyrical/opt/gz_sensors_vendor/lib',
            '/usr/lib/x86_64-linux-gnu/gz-sim-10/plugins',
            os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', ''),
        ) if p
    )
    return LaunchDescription([
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=models_path,
        ),
        SetEnvironmentVariable(name='GZ_SIM_SYSTEM_PLUGIN_PATH', value=gz_plugins),
        SetEnvironmentVariable(name='GZ_PLUGIN_PATH', value=gz_plugins),
        SetEnvironmentVariable(name='LIBGL_ALWAYS_SOFTWARE', value='1'),
        SetEnvironmentVariable(name='LIBGL_DRI3_DISABLE', value='1'),
        world_arg,
        start_follower_arg,
        safety_enable_arg,
        goal_bypass_arg,
        latch_release_arg,
        goal_x_arg,
        goal_y_arg,
        gz_sim,
        bridge,
        OpaqueFunction(function=_contact_bridges),
        OpaqueFunction(function=_sim_nodes),
    ])


def _sim_nodes(context, *args, **kwargs):
    world_path = LaunchConfiguration('world').perform(context)
    world_name = _world_name_from_path(world_path)
    stop_distance = 0.515 if world_name == 'stop_obstacle' else 0.50
    min_trip_pose = 1.0 if world_name == 'stop_obstacle' else 0.55
    self_cull = 0.12 if world_name == 'stop_obstacle' else 0.51
    goal_x = float(LaunchConfiguration('goal_x').perform(context))
    goal_y = float(LaunchConfiguration('goal_y').perform(context))
    return [
        Node(
            package='grc_robot',
            executable='grc_waypoint_follower',
            parameters=[{
                'use_sim_time': True,
                'safety_stop.enable': ParameterValue(
                    LaunchConfiguration('safety_stop_enable'), value_type=bool),
                'safety_stop.require_scan': True,
                'safety_stop.near_goal_bypass': ParameterValue(
                    LaunchConfiguration('goal_safety_bypass'), value_type=bool),
                'safety_stop.latch_release_enable': ParameterValue(
                    LaunchConfiguration('latch_release_enable'), value_type=bool),
                'safety_stop.release_dwell_sec': 2.0,
                'safety_stop.self_return_cull_m': self_cull,
                'safety_stop.trip_confirm_scans': 3,
                'safety_stop.min_trip_pose_x_m': min_trip_pose,
                'stop_distance': stop_distance,
            }],
            condition=IfCondition(LaunchConfiguration('start_follower')),
            output='screen',
        ),
        Node(
            package='grc_bringup',
            executable='publish_waypoints.py',
            name='waypoint_publisher',
            parameters=[{
                'use_sim_time': True,
                'goal_x': goal_x,
                'goal_y': goal_y,
            }],
            condition=IfCondition(LaunchConfiguration('start_follower')),
        ),
    ]
