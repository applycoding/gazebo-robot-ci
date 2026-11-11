// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci — Arpan Bom

#include "grc_robot/waypoint_follower_node.hpp"

#include <chrono>
#include <cmath>
#include <string>

namespace grc_robot
{

WaypointFollowerNode::WaypointFollowerNode(const rclcpp::NodeOptions & options)
: Node("grc_waypoint_follower", options)
{
  declare_parameters();
  load_parameters();
  follower_ = Follower(follower_cfg_);
  safety_ = SafetyStop(safety_cfg_);

  path_sub_ = create_subscription<nav_msgs::msg::Path>(
    "/waypoints", rclcpp::QoS(10),
    [this](const nav_msgs::msg::Path::SharedPtr msg) { on_path(msg); });
  scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
    "/scan", rclcpp::SensorDataQoS(),
    [this](const sensor_msgs::msg::LaserScan::SharedPtr msg) { on_scan(msg); });
  odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
    "/odom", rclcpp::QoS(10),
    [this](const nav_msgs::msg::Odometry::SharedPtr msg) { on_odom(msg); });

  cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
  status_pub_ = create_publisher<std_msgs::msg::String>("/grc/status", 10);

  timer_ = create_wall_timer(std::chrono::milliseconds(20), [this]() { on_control_tick(); });
}

Twist2D WaypointFollowerNode::control_step_for_test(
  const Pose2D & pose,
  const ScanView * scan,
  double now_sec,
  double scan_stamp_sec)
{
  if (waypoints_.empty()) {
    Pose2D wp{4.0, 0.0, 0.0};
    waypoints_.push_back(wp);
    waypoint_index_ = 0;
  }
  last_valid_scan_stamp_ = scan_stamp_sec;
  std::size_t idx = waypoint_index_;
  const Twist2D raw = follower_.step(pose, waypoints_, idx, 0.02);
  waypoint_index_ = idx;
  return safety_.overlay(raw, scan, now_sec, scan_stamp_sec, true);
}

void WaypointFollowerNode::declare_parameters()
{
  declare_parameter("v_cruise", 0.40);
  declare_parameter("v_max", 0.50);
  declare_parameter("omega_max", 1.20);
  declare_parameter("heading_kp", 1.5);
  declare_parameter("goal_tol_xy", 0.20);
  declare_parameter("goal_tol_yaw", 0.30);
  declare_parameter("stop_distance", 0.50);
  declare_parameter("stop_release_margin", 0.10);
  declare_parameter("forward_half_angle_rad", 0.262);
  declare_parameter("scan_timeout", 0.5);
  declare_parameter("safety_stop.enable", true);
  declare_parameter("safety_stop.require_scan", true);
  declare_parameter("safety_stop.near_goal_bypass", false);
  declare_parameter("safety_stop.latch_release_enable", false);
  declare_parameter("safety_stop.release_dwell_sec", 0.0);
  declare_parameter("safety_stop.self_return_cull_m", 0.08);
  declare_parameter("safety_stop.trip_confirm_scans", 1);
  declare_parameter("safety_stop.min_trip_pose_x_m", -1.0);
  declare_parameter("odom_frame", "odom");
  declare_parameter("base_frame", "base_link");
  declare_parameter("laser_frame", "laser_link");
}

void WaypointFollowerNode::load_parameters()
{
  follower_cfg_.v_cruise = get_parameter("v_cruise").as_double();
  follower_cfg_.v_max = get_parameter("v_max").as_double();
  follower_cfg_.omega_max = get_parameter("omega_max").as_double();
  follower_cfg_.heading_kp = get_parameter("heading_kp").as_double();
  follower_cfg_.goal_tol_xy = get_parameter("goal_tol_xy").as_double();
  follower_cfg_.goal_tol_yaw = get_parameter("goal_tol_yaw").as_double();
  safety_cfg_.enable = get_parameter("safety_stop.enable").as_bool();
  safety_cfg_.require_scan = get_parameter("safety_stop.require_scan").as_bool();
  near_goal_safety_bypass_ = get_parameter("safety_stop.near_goal_bypass").as_bool();
  safety_cfg_.latch_release_enable =
    get_parameter("safety_stop.latch_release_enable").as_bool();
  safety_cfg_.release_dwell_sec =
    get_parameter("safety_stop.release_dwell_sec").as_double();
  safety_cfg_.self_return_cull_m = static_cast<float>(
    get_parameter("safety_stop.self_return_cull_m").as_double());
  safety_cfg_.trip_confirm_scans =
    get_parameter("safety_stop.trip_confirm_scans").as_int();
  safety_cfg_.min_trip_pose_x_m =
    get_parameter("safety_stop.min_trip_pose_x_m").as_double();
  follower_cfg_.enable_centerline_bias = safety_cfg_.enable;
  safety_cfg_.stop_distance = get_parameter("stop_distance").as_double();
  safety_cfg_.release_margin = get_parameter("stop_release_margin").as_double();
  safety_cfg_.forward_half_angle_rad = get_parameter("forward_half_angle_rad").as_double();
  safety_cfg_.scan_timeout_sec = get_parameter("scan_timeout").as_double();
}

bool WaypointFollowerNode::scan_has_finite(const sensor_msgs::msg::LaserScan & msg)
{
  for (float r : msg.ranges) {
    if (std::isfinite(r)) {
      return true;
    }
  }
  return false;
}

void WaypointFollowerNode::on_path(const nav_msgs::msg::Path::SharedPtr msg)
{
  waypoints_.clear();
  for (const auto & pose_stamped : msg->poses) {
    Pose2D p;
    p.x = pose_stamped.pose.position.x;
    p.y = pose_stamped.pose.position.y;
      const auto & o = pose_stamped.pose.orientation;
      p.yaw = std::atan2(
        2.0 * (o.w * o.z + o.x * o.y),
        1.0 - 2.0 * (o.y * o.y + o.z * o.z));
    waypoints_.push_back(p);
  }
  waypoint_index_ = 0;
  follower_.reset();
  safety_.reset();
}

void WaypointFollowerNode::on_scan(const sensor_msgs::msg::LaserScan::SharedPtr msg)
{
  last_scan_.ranges = msg->ranges;
  last_scan_.angle_min = msg->angle_min;
  last_scan_.angle_increment = msg->angle_increment;
  last_scan_.range_min = msg->range_min;
  last_scan_.range_max = msg->range_max;
  has_scan_ = true;
  if (scan_has_finite(*msg)) {
    last_valid_scan_stamp_ = rclcpp::Time(msg->header.stamp).seconds();
  }
}

void WaypointFollowerNode::on_odom(const nav_msgs::msg::Odometry::SharedPtr msg)
{
  last_pose_.x = msg->pose.pose.position.x;
  last_pose_.y = msg->pose.pose.position.y;
    const auto & o = msg->pose.pose.orientation;
    last_pose_.yaw = std::atan2(
      2.0 * (o.w * o.z + o.x * o.y),
      1.0 - 2.0 * (o.y * o.y + o.z * o.z));
  has_odom_ = true;
}

void WaypointFollowerNode::on_control_tick()
{
  if (!has_odom_ || waypoints_.empty()) {
    publish_status(DriveState::Idle, StopReason::None);
    return;
  }
  const double now = now_seconds();
  const ScanView * scan_ptr = has_scan_ ? &last_scan_ : nullptr;
  std::size_t idx = waypoint_index_;
  const Twist2D raw = follower_.step(last_pose_, waypoints_, idx, 0.02);
  waypoint_index_ = idx;
  const Pose2D & goal_wp = waypoints_.back();
  const double dist_final = std::hypot(
    goal_wp.x - last_pose_.x, goal_wp.y - last_pose_.y);
  Twist2D out = raw;
  const bool apply_safety = !(near_goal_safety_bypass_ && dist_final < 1.0);
  if (apply_safety) {
    out = safety_.overlay(
      raw, scan_ptr, now, last_valid_scan_stamp_, true, last_pose_.x);
  }

  geometry_msgs::msg::Twist cmd;
  cmd.linear.x = out.v;
  cmd.angular.z = out.omega;
  cmd_pub_->publish(cmd);

  DriveState ds = follower_.state();
  StopReason sr = StopReason::None;
  if (apply_safety) {
    sr = safety_.stop_reason();
    if (safety_.state() == DriveState::ScanTimeout) {
      ds = DriveState::ScanTimeout;
    } else if (
      safety_.state() == DriveState::Stopped || safety_.latched_stop())
    {
      ds = DriveState::Stopped;
      if (sr == StopReason::None) {
        sr = StopReason::Obstacle;
      }
    }
  }
  publish_status(ds, sr);
}

double WaypointFollowerNode::now_seconds() const
{
  return get_clock()->now().seconds();
}

void WaypointFollowerNode::publish_status(DriveState state, StopReason reason)
{
  std::string state_str = "idle";
  switch (state) {
    case DriveState::Idle:
      state_str = "idle";
      break;
    case DriveState::Following:
      state_str = "following";
      break;
    case DriveState::Stopped:
      state_str = "stopped";
      break;
    case DriveState::Arrived:
      state_str = "arrived";
      break;
      case DriveState::ScanTimeout:
        state_str = "scan_timeout";
        break;
      default:
        state_str = "idle";
        break;
    }
    std::string reason_str = "none";
    switch (reason) {
    case StopReason::None:
      reason_str = "none";
      break;
    case StopReason::Obstacle:
      reason_str = "obstacle";
      break;
      case StopReason::ScanTimeout:
        reason_str = "scan_timeout";
        break;
      default:
        reason_str = "none";
        break;
    }
  std_msgs::msg::String msg;
  msg.data =
    "{\"state\":\"" + state_str + "\",\"safety_stop\":" +
    (safety_cfg_.enable ? "true" : "false") + ",\"waypoint_index\":" +
    std::to_string(waypoint_index_) + ",\"stop_reason\":\"" + reason_str + "\"}";
  status_pub_->publish(msg);
}

}  // namespace grc_robot
