# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import launch_testing.actions


def make_sim_launch(
    world_file: str,
    start_follower: str,
    safety_enable: str,
    scenario: str,
    extra_nodes=None,
) -> LaunchDescription:
    bringup_share = get_package_share_directory('grc_bringup')
    robot_share = get_package_share_directory('grc_robot')
    models_path = os.path.join(robot_share, 'models')
    world_path = os.path.join(bringup_share, 'worlds', world_file)
    latch_release = 'false' if scenario == 's2' else 'true'
    goal_bypass = 'true' if scenario in ('s1', 's1_brake_expects_miss') else 'false'

    sim_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'sim.launch.py')),
        launch_arguments={
            'world': world_path,
            'start_follower': start_follower,
            'safety_stop_enable': safety_enable,
            'latch_release_enable': latch_release,
            'goal_safety_bypass': goal_bypass,
        }.items(),
    )

    artifacts = os.environ.get('GRC_ARTIFACTS_DIR', '/ws/artifacts')
    scenario_node = Node(
        package='grc_bringup',
        executable='run_scenario_test.py',
        name='grc_scenario_test',
        output='screen',
        arguments=['--scenario', scenario, '--artifacts-dir', artifacts],
        parameters=[{'use_sim_time': True}],
    )

    gz_plugin_paths = ':'.join(
        p for p in (
            '/opt/ros/lyrical/lib',
            '/opt/ros/lyrical/opt/gz_sim_vendor/lib',
            '/opt/ros/lyrical/opt/gz_plugins_vendor/lib',
            '/opt/ros/lyrical/opt/gz_sensors_vendor/lib',
            '/usr/lib/x86_64-linux-gnu/gz-sim-10/plugins',
            os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', ''),
        ) if p
    )
    domain = str(10 + hash(scenario) % 80)
    actions = [
        SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=models_path),
        SetEnvironmentVariable(name='GZ_SIM_SYSTEM_PLUGIN_PATH', value=gz_plugin_paths),
        SetEnvironmentVariable(name='GZ_PLUGIN_PATH', value=gz_plugin_paths),
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value=domain),
        SetEnvironmentVariable(name='GZ_PARTITION', value=f'grc_{scenario}'),
        sim_include,
    ]
    if extra_nodes:
        actions.extend(extra_nodes)
    actions.append(TimerAction(period=3.0, actions=[scenario_node]))
    actions.append(launch_testing.actions.ReadyToTest())
    return LaunchDescription(actions)


def read_sidecar_pass(scenario: str) -> bool:
    artifacts = Path(os.environ.get('GRC_ARTIFACTS_DIR', '/ws/artifacts'))
    sidecar = artifacts / 'scenarios' / f'{scenario}.json'
    if not sidecar.is_file():
        return False
    data = json.loads(sidecar.read_text(encoding='utf-8'))
    return bool(data.get('pass'))
