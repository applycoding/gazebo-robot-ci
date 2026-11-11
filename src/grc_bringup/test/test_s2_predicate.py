# SPDX-License-Identifier: Apache-2.0

from grc_bringup.sim_test_lib import s2_timeout_fixture_fails


def test_timeout_stop_does_not_pass_s2():
    assert s2_timeout_fixture_fails()
