#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from rclpy.node import Node


class WaypointPublisher(Node):
    def __init__(self):
        super().__init__('grc_waypoint_publisher')
        self.declare_parameter('goal_x', 4.0)
        self.declare_parameter('goal_y', 0.0)
        self.goal_x = float(self.get_parameter('goal_x').value)
        self.goal_y = float(self.get_parameter('goal_y').value)
        self.pub = self.create_publisher(Path, '/waypoints', 10)
        self.timer = self.create_timer(0.25, self.publish_once)
        self.sent = False

    def publish_once(self):
        if self.sent:
            return
        msg = Path()
        msg.header.frame_id = 'odom'
        msg.header.stamp = self.get_clock().now().to_msg()
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose.position.x = self.goal_x
        pose.pose.position.y = self.goal_y
        q = self._yaw_quat(0.0)
        pose.pose.orientation.x = q[0]
        pose.pose.orientation.y = q[1]
        pose.pose.orientation.z = q[2]
        pose.pose.orientation.w = q[3]
        msg.poses.append(pose)
        self.pub.publish(msg)
        self.sent = True

    @staticmethod
    def _yaw_quat(yaw):
        return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


def main():
    rclpy.init()
    node = WaypointPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
