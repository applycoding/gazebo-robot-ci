# SPDX-License-Identifier: Apache-2.0

import time
import unittest

import launch_testing

from grc_bringup.launch_test_lib import make_sim_launch, read_sidecar_pass


def generate_test_description():
    return make_sim_launch('stop_obstacle.sdf', 'true', 'false', 's2_mutant_expects_contact')


@launch_testing.pre_shutdown_test()
class TestS2Mutant(unittest.TestCase):
    def test_wait_for_sidecar(self):
        for _ in range(180):
            if read_sidecar_pass('s2_mutant_expects_contact'):
                return
            time.sleep(1)
        self.fail('mutant sidecar missing or not passing within 180s')


@launch_testing.post_shutdown_test()
class TestS2MutantPost(unittest.TestCase):
    def test_sidecar_pass(self):
        assert read_sidecar_pass('s2_mutant_expects_contact'), 'mutant sidecar missing or not passing'
