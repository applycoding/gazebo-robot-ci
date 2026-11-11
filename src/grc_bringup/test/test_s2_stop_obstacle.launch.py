# SPDX-License-Identifier: Apache-2.0

import time
import unittest

import launch_testing

from grc_bringup.launch_test_lib import make_sim_launch, read_sidecar_pass


def generate_test_description():
    return make_sim_launch('stop_obstacle.sdf', 'true', 'true', 's2')


@launch_testing.pre_shutdown_test()
class TestS2StopObstacle(unittest.TestCase):
    def test_wait_for_sidecar(self):
        for _ in range(180):
            if read_sidecar_pass('s2'):
                return
            time.sleep(1)
        self.fail('s2 sidecar missing or not passing within 180s')


@launch_testing.post_shutdown_test()
class TestS2StopObstaclePost(unittest.TestCase):
    def test_sidecar_pass(self):
        assert read_sidecar_pass('s2'), 's2 scenario sidecar missing or not passing'
