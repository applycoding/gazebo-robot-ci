// SPDX-License-Identifier: Apache-2.0

#include <memory>

#include "grc_robot/waypoint_follower_node.hpp"
#include "rclcpp/rclcpp.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<grc_robot::WaypointFollowerNode>());
  rclcpp::shutdown();
  return 0;
}
