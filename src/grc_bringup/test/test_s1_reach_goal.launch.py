# SPDX-License-Identifier: Apache-2.0

import time
import unittest

import launch_testing

from grc_bringup.launch_test_lib import make_sim_launch, read_sidecar_pass


def generate_test_description():
    return make_sim_launch('reach_goal.sdf', 'true', 'true', 's1')


@launch_testing.pre_shutdown_test()
class TestS1ReachGoal(unittest.TestCase):
    def test_wait_for_sidecar(self):
        for _ in range(240):
            if read_sidecar_pass('s1'):
                return
            time.sleep(1)
        self.fail('s1 sidecar missing or not passing within 240s')


@launch_testing.post_shutdown_test()
class TestS1ReachGoalPost(unittest.TestCase):
    def test_sidecar_pass(self):
        assert read_sidecar_pass('s1'), 's1 scenario sidecar missing or not passing'
