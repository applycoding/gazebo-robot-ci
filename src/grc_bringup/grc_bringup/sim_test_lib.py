# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import Any

BOX_CENTER = (2.0, 0.0)
BOX_HALF = 0.20
ROBOT_RADIUS = 0.15
GOAL = (4.0, 0.0, 0.0)
GOAL_TOL_XY = 0.20
GOAL_TOL_YAW = 0.30


def circle_aabb_clearance(x: float, y: float) -> float:
    dx = max(abs(x - BOX_CENTER[0]) - BOX_HALF, 0.0)
    dy = max(abs(y - BOX_CENTER[1]) - BOX_HALF, 0.0)
    return math.hypot(dx, dy) - ROBOT_RADIUS


def parse_status_json(data: str) -> dict[str, Any]:
    return json.loads(data)


def s2_pass_predicate(row: dict[str, Any]) -> bool:
    if row.get('reason') == 'scan_timeout':
        return False
    if row.get('observed') == 'scan_timeout':
        return False
    if row.get('trip_range_m') is None:
        return False
    if row.get('stop_reason') != 'obstacle' and row.get('observed') != 'obstacle_stop':
        return False
    trip = row.get('trip_range_m', 999.0)
    if trip >= 0.50:
        return False
    return bool(row.get('pass'))


def s2_timeout_fixture_fails() -> bool:
    fixture = {
        'name': 's2',
        'pass': False,
        'reason': 'scan_timeout',
        'observed': 'scan_timeout',
        'trip_range_m': None,
        'stop_reason': 'scan_timeout',
    }
    return not s2_pass_predicate(fixture)


def _contact_pair_text(pair) -> str:
    chunks: list[str] = []
    for side in ('collision1', 'collision2', 'world1', 'world2'):
        ent = getattr(pair, side, None)
        if ent is None:
            continue
        name = getattr(ent, 'name', '') or ''
        if name:
            chunks.append(str(name))
        ent_id = getattr(ent, 'id', None)
        if ent_id is not None and str(ent_id):
            chunks.append(str(ent_id))
    return ' '.join(chunks).lower()


def _is_ground_contact(text: str) -> bool:
    return 'ground' in text or 'plane' in text


def _is_box_contact(text: str) -> bool:
    return 'obstacle_box' in text


def _is_robot_contact(text: str) -> bool:
    if any(tok in text for tok in ('grc_robot', 'grc_diff', 'base_link')):
        return True
    if 'wheel' in text or 'body_collision' in text or '::lc' in text or '::rc' in text:
        return True
    return False


def obstacle_contact_pair_count(contact_msg) -> int:
    count = 0
    for pair in contact_msg.contacts:
        text = _contact_pair_text(pair)
        if _is_ground_contact(text):
            continue
        if _is_box_contact(text) and _is_robot_contact(text):
            count += 1
        elif _is_box_contact(text) and _is_robot_contact(text):
            count += 1
    return count


def is_robot_box_contact(contact_msg, robot_names: tuple[str, ...] = ('grc_robot', 'grc_diff')):
    blob = str(contact_msg).lower()
    if _is_box_contact(blob) and (
        any(r.lower() in blob for r in robot_names) or 'base_link' in blob or 'wheel' in blob
    ):
        return True
    for pair in contact_msg.contacts:
        text = _contact_pair_text(pair)
        if _is_ground_contact(text):
            continue
        if _is_box_contact(text) and (
            _is_robot_contact(text) or any(r.lower() in text for r in robot_names)
        ):
            return True
    return False


def ignore_ground_contact(contact_msg) -> int:
    count = 0
    for pair in contact_msg.contacts:
        text = _contact_pair_text(pair)
        if _is_ground_contact(text):
            continue
        if _is_box_contact(text):
            count += 1
    return count


@dataclass
class Telemetry:
    scenario: str
    expected: str
    sim_duration_s: float
    samples: list[dict[str, float]] = field(default_factory=list)
    last_sample_t: float = -1.0
    contact_count: int = 0
    contact_sensor_alive: bool = False
    box_touch_fired: bool = False
    min_clearance_m: float = 999.0
    max_abs_y: float = 0.0
    min_forward_range: float = 999.0
    trip_range_m: float | None = None
    trip_sim_time: float | None = None
    saw_following_to_stopped: bool = False
    stop_reason: str = 'none'
    final_state: str = 'idle'
    scan_timeout_seen: bool = False
    final_xy_err: float = 999.0
    final_yaw_err: float = 999.0
    cmd_zeros_after_trip: bool = False
    speed_low_after_trip: bool = False

    def record_pose(self, t_sim: float, x: float, y: float, yaw: float) -> None:
        self.max_abs_y = max(self.max_abs_y, abs(y))
        if self.scenario in ('s2', 's2_mutant_expects_contact'):
            self.min_clearance_m = min(self.min_clearance_m, circle_aabb_clearance(x, y))
        self.final_xy_err = math.hypot(GOAL[0] - x, GOAL[1] - y)
        dyaw = yaw - GOAL[2]
        while dyaw > math.pi:
            dyaw -= 2.0 * math.pi
        while dyaw <= -math.pi:
            dyaw += 2.0 * math.pi
        self.final_yaw_err = abs(dyaw)
        if t_sim - self.last_sample_t >= 0.05 or self.last_sample_t < 0:
            self.samples.append({'t_sim': t_sim, 'x': x, 'y': y, 'yaw': yaw})
            self.last_sample_t = t_sim

    def write_sidecar(self, path: str, pass_gate: bool, observed: str, reason: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            'name': self.scenario,
            'pass': pass_gate,
            'expected': self.expected,
            'observed': observed,
            'sim_duration_s': self.sim_duration_s,
            'wall_duration_s': 0.0,
            'time_to_goal_s': None,
            'time_to_stop_s': self.trip_sim_time,
            'trip_range_m': self.trip_range_m,
            'min_forward_range_m': (
                None if self.min_forward_range > 900 else self.min_forward_range),
            'min_clearance_m': self.min_clearance_m,
            'contact_count': self.contact_count,
            'data_health': 'ok',
            'reason': reason,
            'stop_reason': self.stop_reason,
            'final_state': self.final_state,
            'final_xy_err_m': self.final_xy_err,
            'final_yaw_err_rad': self.final_yaw_err,
            'contact_sensor_alive': self.contact_sensor_alive,
            'box_touch_fired': self.box_touch_fired,
            'trajectory_samples': self.samples,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)


def yaw_from_quat(q) -> float:
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def min_forward_scan_range(scan, cull_below_m: float = 0.08) -> float | None:
    if not scan.ranges:
        return None
    best = 999.0
    for i, r in enumerate(scan.ranges):
        if not math.isfinite(r) or r < scan.range_min or r > scan.range_max:
            continue
        if r < cull_below_m:
            continue
        angle = scan.angle_min + i * scan.angle_increment
        if abs(angle) > 0.262:
            continue
        best = min(best, float(r))
    return best if best < 900 else None


def parse_status_state(status_data: str) -> tuple[str, str]:
    try:
        obj = json.loads(status_data)
        return str(obj.get('state', 'idle')), str(obj.get('stop_reason', 'none'))
    except json.JSONDecodeError:
        return 'idle', 'none'
