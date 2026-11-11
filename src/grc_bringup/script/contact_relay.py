#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import argparse

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from ros_gz_interfaces.msg import Contacts


class ContactRelay(Node):
    """Forward gz-bridged Contacts streams onto the shared /contacts oracle topic."""

    def __init__(self, source_topics: list[str]) -> None:
        super().__init__('grc_contact_relay')
        qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self._pub = self.create_publisher(Contacts, '/contacts', qos)
        for topic in source_topics:
            self.create_subscription(
                Contacts,
                topic,
                self._forward,
                qos,
            )
        self.get_logger().info(
            f'relaying {len(source_topics)} contact source(s) -> /contacts')

    def _forward(self, msg: Contacts) -> None:
        self._pub.publish(msg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--sources',
        nargs='+',
        default=['/contacts_wheel'],
        help='ROS contact topics to merge onto /contacts',
    )
    args, _unknown = parser.parse_known_args()
    rclpy.init()
    node = ContactRelay(args.sources)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
