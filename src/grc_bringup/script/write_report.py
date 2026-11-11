#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HONESTY = (
    'Simulation only; recorded CI run from headless gz sim. '
    'This JSON is not a live simulator.'
)

SCENARIO_ORDER = (
    's1',
    's2',
    's2_mutant_expects_contact',
    's1_brake_expects_miss',
)


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'unknown'


def gz_version() -> str:
    for cmd in (['gz', 'sim', '--version'], ['gz', '--versions']):
        try:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return 'unknown'


def load_sidecar(artifacts: Path, name: str) -> tuple[dict[str, Any], list[dict[str, float]]]:
    path = artifacts / 'scenarios' / f'{name}.json'
    if not path.is_file():
        return {
            'name': name,
            'pass': False,
            'expected': name,
            'observed': 'infra_failure',
            'sim_duration_s': 0.0,
            'wall_duration_s': 0.0,
            'time_to_goal_s': None,
            'time_to_stop_s': None,
            'trip_range_m': None,
            'min_forward_range_m': None,
            'min_clearance_m': 0.0,
            'contact_count': 0,
            'data_health': 'missing',
            'reason': 'missing_sidecar',
        }, []
    with open(path, encoding='utf-8') as f:
        row = json.load(f)
    traj = row.pop('trajectory_samples', [])
    row.setdefault('time_to_goal_s', None)
    row.setdefault('time_to_stop_s', None)
    row.setdefault('trip_range_m', None)
    row.setdefault('min_forward_range_m', None)
    return row, traj


def main():
    artifacts = Path(os.environ.get('GRC_ARTIFACTS_DIR', '/ws/artifacts'))
    artifacts.mkdir(parents=True, exist_ok=True)
    scenarios = []
    trajectories = []
    for name in SCENARIO_ORDER:
        row, samples = load_sidecar(artifacts, name)
        scenarios.append(row)
        trajectories.append({'name': name, 'samples': samples})

    report = {
        'report_version': 1,
        'git_sha': git_sha(),
        'run_id': os.environ.get('GITHUB_RUN_ID', 'local'),
        'run_url': os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
        + '/'
        + os.environ.get('GITHUB_REPOSITORY', 'applycoding/gazebo-robot-ci')
        + '/actions/runs/'
        + os.environ.get('GITHUB_RUN_ID', '0'),
        'runner_image': os.environ.get('ImageVersion', os.environ.get('ImageOS', 'unknown')),
        'ros_distro': 'lyrical',
        'gz_version': gz_version(),
        'sample': False,
        'honesty': HONESTY,
        'scenarios': scenarios,
        'trajectories': trajectories,
    }
    out = artifacts / 'ci-report.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    md_path = artifacts / 'ci-report.md'
    lines = ['# CI report', '', f'SHA: `{report["git_sha"]}`', '']
    for row in scenarios:
        lines.append(
            f'- **{row["name"]}**: pass={row["pass"]} expected={row["expected"]} '
            f'observed={row["observed"]}')
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
