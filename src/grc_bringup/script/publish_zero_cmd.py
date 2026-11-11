#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class ZeroCmdPublisher(Node):
    def __init__(self):
        super().__init__('grc_zero_cmd')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(0.05, self._tick)

    def _tick(self):
        msg = Twist()
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ZeroCmdPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
