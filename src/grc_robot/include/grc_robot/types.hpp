// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci — Arpan Bom

#ifndef GRC_ROBOT__TYPES_HPP_
#define GRC_ROBOT__TYPES_HPP_

namespace grc_robot
{

struct Pose2D
{
  double x{0.0};
  double y{0.0};
  double yaw{0.0};
};

struct Twist2D
{
  double v{0.0};
  double omega{0.0};
};

struct FollowerConfig
{
  double v_cruise{0.40};
  double v_max{0.50};
  double omega_max{1.20};
  double goal_tol_xy{0.20};
  double goal_tol_yaw{0.30};
  double heading_kp{1.5};
  bool enable_centerline_bias{true};
};

struct SafetyConfig
{
  bool enable{true};
  bool require_scan{true};
  double stop_distance{0.50};
  double release_margin{0.10};
  double forward_half_angle_rad{0.262};
  double scan_timeout_sec{0.5};
  bool latch_release_enable{false};
  double release_dwell_sec{0.0};
  float self_return_cull_m{0.08f};
  int trip_confirm_scans{1};
  double min_trip_pose_x_m{-1.0};
};

enum class DriveState
{
  Idle,
  Following,
  Stopped,
  Arrived,
  ScanTimeout
};

enum class StopReason
{
  None,
  Obstacle,
  ScanTimeout
};

}  // namespace grc_robot

#endif  // GRC_ROBOT__TYPES_HPP_
