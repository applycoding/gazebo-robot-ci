# SPDX-License-Identifier: Apache-2.0

import time
import unittest

import launch_testing
from launch_ros.actions import Node

from grc_bringup.launch_test_lib import make_sim_launch, read_sidecar_pass


def generate_test_description():
    zero_cmd = Node(
        package='grc_bringup',
        executable='publish_zero_cmd.py',
        parameters=[{'use_sim_time': True}],
    )
    return make_sim_launch(
        'reach_goal.sdf', 'false', 'true', 's1_brake_expects_miss', extra_nodes=[zero_cmd])


@launch_testing.pre_shutdown_test()
class TestS1Brake(unittest.TestCase):
    def test_wait_for_sidecar(self):
        for _ in range(240):
            if read_sidecar_pass('s1_brake_expects_miss'):
                return
            time.sleep(1)
        self.fail('brake sidecar missing or not passing within 240s')


@launch_testing.post_shutdown_test()
class TestS1BrakePost(unittest.TestCase):
    def test_sidecar_pass(self):
        assert read_sidecar_pass('s1_brake_expects_miss'), 'brake sidecar missing or not passing'
