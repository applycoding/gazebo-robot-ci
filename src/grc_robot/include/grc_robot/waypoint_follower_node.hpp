// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci - Arpan Bom

#ifndef GRC_ROBOT__WAYPOINT_FOLLOWER_NODE_HPP_
#define GRC_ROBOT__WAYPOINT_FOLLOWER_NODE_HPP_

#include <memory>
#include <vector>

#include "grc_robot/follower.hpp"
#include "grc_robot/safety_stop.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "nav_msgs/msg/path.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/string.hpp"

namespace grc_robot
{

class WaypointFollowerNode : public rclcpp::Node
{
public:
  explicit WaypointFollowerNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

  Twist2D control_step_for_test(
    const Pose2D & pose,
    const ScanView * scan,
    double now_sec,
    double scan_stamp_sec);

private:
  void declare_parameters();
  void load_parameters();
  void on_path(const nav_msgs::msg::Path::SharedPtr msg);
  void on_scan(const sensor_msgs::msg::LaserScan::SharedPtr msg);
  void on_odom(const nav_msgs::msg::Odometry::SharedPtr msg);
  void on_control_tick();
  double now_seconds() const;
  void publish_status(DriveState state, StopReason reason);
  static bool scan_has_finite(const sensor_msgs::msg::LaserScan & msg);

  FollowerConfig follower_cfg_;
  SafetyConfig safety_cfg_;
  Follower follower_;
  SafetyStop safety_;

  std::vector<Pose2D> waypoints_;
  std::size_t waypoint_index_{0};
  Pose2D last_pose_{};
  ScanView last_scan_{};
  bool has_scan_{false};
  bool has_odom_{false};
  bool near_goal_safety_bypass_{false};
  double last_valid_scan_stamp_{-1.0};

  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr path_sub_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace grc_robot

#endif  // GRC_ROBOT__WAYPOINT_FOLLOWER_NODE_HPP_
