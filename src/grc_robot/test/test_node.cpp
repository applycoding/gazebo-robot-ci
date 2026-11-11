// SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>
#include <memory>
#include <limits>
#include <vector>

#include "grc_robot/waypoint_follower_node.hpp"
#include "rclcpp/rclcpp.hpp"

TEST(NodeTest, ConstructAndStepWithoutGz)
{
  rclcpp::init(0, nullptr);
  rclcpp::NodeOptions opts;
  opts.use_global_arguments(false);
  opts.automatically_declare_parameters_from_overrides(false);
  auto node = std::make_shared<grc_robot::WaypointFollowerNode>(opts);
  grc_robot::ScanView scan;
  scan.angle_min = -3.14159F;
  scan.angle_increment = 0.0348F;
  scan.range_min = 0.08F;
  scan.range_max = 10.0F;
  scan.ranges.assign(181, std::numeric_limits<float>::infinity());
  const grc_robot::Twist2D out =
    node->control_step_for_test(grc_robot::Pose2D{0, 0, 0}, &scan, 0.1, 0.1);
  EXPECT_GT(out.v, 0.0);
  rclcpp::shutdown();
}
