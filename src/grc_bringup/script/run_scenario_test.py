#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import math
import os
import subprocess
import sys
import time

import rclpy
from rclpy.parameter import Parameter
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from ros_gz_interfaces.msg import Contacts
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String

from grc_bringup.sim_test_lib import (
    GOAL,
    GOAL_TOL_XY,
    GOAL_TOL_YAW,
    Telemetry,
    ignore_ground_contact,
    is_robot_box_contact,
    obstacle_contact_pair_count,
    min_forward_scan_range,
    parse_status_state,
    yaw_from_quat,
)


_GZ_WHEEL_CONTACT = {
    's1': (
        '/world/reach_goal/model/grc_robot/link/left_wheel/sensor/lc_contact/contacts'
    ),
    's1_brake_expects_miss': (
        '/world/reach_goal/model/grc_robot/link/left_wheel/sensor/lc_contact/contacts'
    ),
    's2': (
        '/world/stop_obstacle/model/grc_robot/link/left_wheel/sensor/lc_contact/contacts'
    ),
    's2_mutant_expects_contact': (
        '/world/stop_obstacle/model/grc_robot/link/left_wheel/sensor/lc_contact/contacts'
    ),
}


def _gz_contact_topic_alive(topic: str) -> bool:
    proc = subprocess.run(
        ['timeout', '4', 'gz', 'topic', '-e', '-t', topic, '-n', '1'],
        capture_output=True,
        env=os.environ.copy(),
    )
    return proc.returncode == 0


class ScenarioTest(Node):
    def __init__(self, scenario: str, artifacts_dir: str):
        super().__init__(
            'grc_scenario_test',
            parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)],
        )
        self.scenario = scenario
        self.artifacts_dir = artifacts_dir
        limits = {
            's1': 20.0,
            's2': 15.0,
            's2_mutant_expects_contact': 15.0,
            's1_brake_expects_miss': 20.0,
        }
        self.t_max = limits[scenario]
        expected = {
            's1': 'reach_goal',
            's2': 'obstacle_stop',
            's2_mutant_expects_contact': 'box_contact',
            's1_brake_expects_miss': 'miss_goal',
        }
        self.tel = Telemetry(scenario, expected[scenario], self.t_max)
        self.prev_state = 'idle'
        self.last_cmd = Twist()
        self.last_odom_v = 0.0
        self.trip_seen = False
        self.trip_time = None
        self.cmd_low_ok = False
        self.speed_low_ok = False
        self.clock_prev = None
        self.clock_stuck_since = None
        self.ready = {'clock': False, 'odom': False, 'scan': False, 'contact': False}
        self.motion_x_started = False
        self.wall_start = time.time()
        self.done = False
        self._exit_code = 1
        self.last_forward_range = None
        self.box_touch_fired = False

        scan_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        contact_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.create_subscription(LaserScan, '/scan', self._on_scan, scan_qos)
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        for topic in ('/contacts', '/contacts_wheel', '/contacts_body'):
            self.create_subscription(Contacts, topic, self._on_contacts, contact_qos)
        self.create_subscription(Bool, '/box_touch', self._on_box_touch, contact_qos)
        self.create_subscription(Twist, '/cmd_vel', self._on_cmd, 10)
        self.create_subscription(String, '/grc/status', self._on_status, 10)
        from rosgraph_msgs.msg import Clock
        self.create_subscription(Clock, '/clock', self._on_clock, 10)
        self.create_timer(0.05, self._tick)

    def _sim_now(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def _on_clock(self, msg):
        t = msg.clock.sec + msg.clock.nanosec / 1e9
        if self.clock_prev is not None and abs(t - self.clock_prev) < 1e-9:
            if self.clock_stuck_since is None:
                self.clock_stuck_since = time.time()
        else:
            self.clock_stuck_since = None
        self.clock_prev = t
        self.ready['clock'] = True

    def _on_scan(self, msg: LaserScan):
        self.ready['scan'] = True
        m = min_forward_scan_range(msg)
        if m is not None:
            self.last_forward_range = m
            self.tel.min_forward_range = min(self.tel.min_forward_range, m)

    def _on_odom(self, msg: Odometry):
        self.ready['odom'] = True
        t = self._sim_now()
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        yaw = yaw_from_quat(msg.pose.pose.orientation)
        self.tel.record_pose(t, x, y, yaw)
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        self.last_odom_v = math.hypot(vx, vy)
        if x > 0.20:
            self.motion_x_started = True

    def _on_box_touch(self, msg: Bool):
        if msg.data:
            self.box_touch_fired = True
            self.tel.box_touch_fired = True
            self.ready['contact'] = True
            self.tel.contact_sensor_alive = True
            self.tel.contact_count = max(self.tel.contact_count, 1)

    def _on_contacts(self, msg: Contacts):
        self.ready['contact'] = True
        self.tel.contact_sensor_alive = True
        box_hits = obstacle_contact_pair_count(msg)
        if box_hits > 0:
            self.tel.contact_count += box_hits
        elif is_robot_box_contact(msg):
            self.tel.contact_count += max(1, len(msg.contacts))

    def _on_cmd(self, msg: Twist):
        self.last_cmd = msg

    def _on_status(self, msg: String):
        state, reason = parse_status_state(msg.data)
        self.tel.final_state = state
        self.tel.stop_reason = reason
        if reason == 'scan_timeout':
            self.tel.scan_timeout_seen = True
        if self.prev_state == 'following' and state == 'stopped':
            self.tel.saw_following_to_stopped = True
            if reason == 'obstacle' and self.tel.samples:
                x_pose = self.tel.samples[-1]['x']
                if x_pose < 0.5:
                    pass
                else:
                    t = self._sim_now()
                    m = self.last_forward_range
                    if m is None:
                        m = self.tel.min_forward_range
                    if m < 0.50 and (
                        self.tel.trip_range_m is None or x_pose > 1.0
                    ):
                        self.tel.trip_range_m = m
                        self.tel.trip_sim_time = t
                        self.trip_seen = True
                        self.trip_time = t
        self.prev_state = state

    def _tick(self):
        if self.done:
            return
        t = self._sim_now()
        if self.clock_stuck_since and time.time() - self.clock_stuck_since > 30.0:
            self._finish(False, 'infra_failure', 'clock_frozen')
            return
        if time.time() - self.wall_start > 600:
            self._finish(False, 'infra_failure', 'wall_watchdog')
            return

        if t >= self.t_max:
            self._evaluate_end(t)
            return

        if self.trip_seen and self.trip_time is not None:
            dt = t - self.trip_time
            if dt <= 0.20:
                if abs(self.last_cmd.linear.x) <= 0.02 and abs(self.last_cmd.angular.z) <= 0.05:
                    self.cmd_low_ok = True
            if dt >= 1.0 and self.last_odom_v <= 0.03:
                self.speed_low_ok = True
            if (
                self.scenario == 's2'
                and self.tel.trip_range_m is not None
                and self.tel.trip_range_m < 0.50
                and not self.trip_seen
            ):
                pass

        if (
            self.scenario == 's2'
            and self.tel.saw_following_to_stopped
            and self.tel.stop_reason == 'obstacle'
            and self.tel.trip_range_m is None
            and self.tel.min_forward_range < 0.50
        ):
            self.trip_seen = True
            self.trip_time = t
            self.tel.trip_range_m = self.tel.min_forward_range
            self.tel.trip_sim_time = t

    def _evaluate_end(self, t: float) -> None:
        contact_ready = self.ready['contact'] or self.scenario in (
            's1', 's1_brake_expects_miss')
        core_ready = (
            self.ready['clock']
            and self.ready['odom']
            and self.ready['scan']
            and contact_ready
        )
        if self.scenario == 's1':
            ok = (
                core_ready
                and self.tel.contact_count == 0
                and self.tel.final_xy_err <= GOAL_TOL_XY
                and self.tel.final_yaw_err <= GOAL_TOL_YAW
                and self.tel.final_state == 'arrived'
                and not self.tel.scan_timeout_seen
                and self.tel.max_abs_y <= 0.35
                and self.motion_x_started
            )
            obs = 'reach_goal' if ok else 'infra_failure'
            self._finish(ok, obs, 's1_gate')

        elif self.scenario == 's2':
            if (
                self.tel.trip_range_m is None
                and self.tel.final_state == 'stopped'
                and self.tel.stop_reason == 'obstacle'
                and self.tel.min_forward_range < 0.50
            ):
                self.tel.trip_range_m = self.tel.min_forward_range
                if self.tel.samples:
                    self.tel.trip_sim_time = self.tel.samples[-1]['t_sim']
                self.trip_seen = True
            if self.tel.final_state == 'stopped' and self.tel.stop_reason == 'obstacle':
                if not self.cmd_low_ok:
                    self.cmd_low_ok = (
                        abs(self.last_cmd.linear.x) <= 0.02
                        and abs(self.last_cmd.angular.z) <= 0.05
                    )
                if not self.speed_low_ok:
                    self.speed_low_ok = self.last_odom_v <= 0.03
            saw_stop = self.tel.saw_following_to_stopped or (
                self.tel.trip_range_m is not None
                and self.tel.stop_reason == 'obstacle'
                and self.tel.final_state == 'stopped'
            )
            max_x = max((s['x'] for s in self.tel.samples), default=0.0)
            ok = (
                core_ready
                and self.motion_x_started
                and self.tel.trip_range_m is not None
                and self.tel.trip_range_m < 0.50
                and saw_stop
                and self.tel.final_state == 'stopped'
                and self.tel.stop_reason == 'obstacle'
                and not self.tel.scan_timeout_seen
                and self.cmd_low_ok
                and self.speed_low_ok
                and self.tel.contact_count == 0
                and self.tel.min_clearance_m >= 0.15
                and max_x < 2.0
            )
            obs = 'obstacle_stop' if ok else (
                'scan_timeout' if self.tel.scan_timeout_seen else 'infra_failure')
            self._finish(ok, obs, 's2_gate')

        elif self.scenario == 's2_mutant_expects_contact':
            physics_touch = (
                self.tel.contact_count > 0
                or self.tel.box_touch_fired
                or self.tel.min_clearance_m < 0.0
            )
            ok = (
                core_ready
                and (self.tel.contact_sensor_alive or self.tel.box_touch_fired)
                and physics_touch
                and not self.tel.scan_timeout_seen
            )
            obs = 'box_contact' if ok else 'infra_failure'
            self._finish(ok, obs, 'mutant_gate')

        elif self.scenario == 's1_brake_expects_miss':
            ok = (
                self.ready['clock']
                and self.ready['odom']
                and self.tel.final_xy_err > GOAL_TOL_XY
            )
            obs = 'miss_goal' if ok else 'infra_failure'
            self._finish(ok, obs, 'brake_gate')

    def _finish(self, pass_gate: bool, observed: str, reason: str) -> None:
        self.done = True
        sidecar = os.path.join(
            self.artifacts_dir, 'scenarios', f'{self.scenario}.json')
        self.tel.write_sidecar(sidecar, pass_gate, observed, reason)
        self.get_logger().info(
            f'scenario {self.scenario} pass={pass_gate} observed={observed}')
        self._exit_code = 0 if pass_gate else 1
        self.done = True
        rclpy.shutdown()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--artifacts-dir', default='/ws/artifacts')
    parser.add_argument('--wait-ready', type=float, default=30.0)
    args = parser.parse_args()

    rclpy.init()
    node = ScenarioTest(args.scenario, args.artifacts_dir)
    deadline = time.time() + args.wait_ready
    while time.time() < deadline and rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.1)
        if all(node.ready.values()):
            break
    if not node.ready['contact']:
        if node.scenario in ('s1', 's1_brake_expects_miss'):
            if node.ready['clock'] and node.ready['odom'] and node.ready['scan']:
                node.ready['contact'] = True
        elif node.tel.contact_sensor_alive:
            node.ready['contact'] = True
        else:
            gz_topic = _GZ_WHEEL_CONTACT.get(node.scenario)
            if gz_topic and _gz_contact_topic_alive(gz_topic):
                node.ready['contact'] = True
                node.tel.contact_sensor_alive = True
    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.05)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
    sys.exit(getattr(node, '_exit_code', 1))


if __name__ == '__main__':
    main()
