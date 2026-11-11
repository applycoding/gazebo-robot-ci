# SPDX-License-Identifier: Apache-2.0

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'script' / 'run_scenario_launch_test.sh'
ARTIFACTS = Path(os.environ.get('GRC_ARTIFACTS_DIR', '/ws/artifacts'))


def _run(case: str, world: str, follower: str, safety: str) -> None:
    subprocess.run(
        ['bash', str(SCRIPT), case, world, follower, safety],
        check=True,
        cwd=ROOT,
    )
    sidecar = ARTIFACTS / 'scenarios' / f'{case}.json'
    assert sidecar.is_file(), f'missing sidecar {sidecar}'
    data = json.loads(sidecar.read_text(encoding='utf-8'))
    assert data.get('pass'), json.dumps(data, indent=2)


def test_s1_reach_goal() -> None:
    _run('s1', 'reach_goal.sdf', 'true', 'true')


def test_s2_stop_obstacle() -> None:
    _run('s2', 'stop_obstacle.sdf', 'true', 'true')


def test_s2_mutant_expects_contact() -> None:
    _run('s2_mutant_expects_contact', 'stop_obstacle.sdf', 'true', 'false')


def test_s1_brake_expects_miss() -> None:
    _run('s1_brake_expects_miss', 'reach_goal.sdf', 'false', 'true')
