// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci — Arpan Bom

#include "grc_robot/safety_stop.hpp"

#include <cmath>
#include <limits>

namespace grc_robot
{

SafetyStop::SafetyStop()
: SafetyStop(SafetyConfig{})
{
}

SafetyStop::SafetyStop(SafetyConfig config)
: config_(config)
{
}

void SafetyStop::reset()
{
  state_ = DriveState::Idle;
  stop_reason_ = StopReason::None;
  latched_stop_ = false;
  last_trip_range_m_ = -1.0;
  latch_trip_time_sec_ = -1.0;
  release_clear_since_sec_ = -1.0;
  first_command_time_set_ = false;
  first_command_time_sec_ = 0.0;
  trip_confirm_count_ = 0;
}

bool SafetyStop::scan_is_valid(const ScanView & scan) const
{
  if (scan.ranges.empty()) {
    return false;
  }
  for (float r : scan.ranges) {
    if (std::isfinite(r)) {
      return true;
    }
  }
  return false;
}

float SafetyStop::min_forward_finite_range(const ScanView & scan) const
{
  float min_r = std::numeric_limits<float>::infinity();
  const std::size_t n = scan.ranges.size();
  for (std::size_t i = 0; i < n; ++i) {
    const float r = scan.ranges[i];
    if (!std::isfinite(r) || r < scan.range_min || r > scan.range_max) {
      continue;
    }
    if (r < config_.self_return_cull_m) {
      continue;
    }
    const double angle = static_cast<double>(scan.angle_min) +
      static_cast<double>(i) * static_cast<double>(scan.angle_increment);
    if (std::abs(angle) > config_.forward_half_angle_rad) {
      continue;
    }
    if (r < min_r) {
      min_r = r;
    }
  }
  return min_r;
}

Twist2D SafetyStop::overlay(
  const Twist2D & cmd,
  const ScanView * scan,
  double now_sec,
  double last_valid_scan_stamp_sec,
  bool commanding,
  double pose_x_m)
{
  if (commanding && !first_command_time_set_) {
    first_command_time_set_ = true;
    first_command_time_sec_ = now_sec;
  }

  if (config_.require_scan && commanding) {
    const bool fresh =
      last_valid_scan_stamp_sec >= 0.0 &&
      (now_sec - last_valid_scan_stamp_sec) <= config_.scan_timeout_sec;
    if (!fresh && (now_sec - first_command_time_sec_) > config_.scan_timeout_sec) {
      state_ = DriveState::ScanTimeout;
      stop_reason_ = StopReason::ScanTimeout;
      return Twist2D{0.0, 0.0};
    }
  }

  if (!config_.enable) {
    if (state_ == DriveState::ScanTimeout) {
      return Twist2D{0.0, 0.0};
    }
    state_ = DriveState::Following;
    stop_reason_ = StopReason::None;
    return cmd;
  }

  if (scan == nullptr || !scan_is_valid(*scan)) {
    if (latched_stop_) {
      state_ = DriveState::Stopped;
      stop_reason_ = StopReason::Obstacle;
      return Twist2D{0.0, 0.0};
    }
    state_ = DriveState::Following;
    stop_reason_ = StopReason::None;
    return cmd;
  }

  const float min_fwd = min_forward_finite_range(*scan);
  const double release_threshold = config_.stop_distance + config_.release_margin;

  const bool pose_ok =
    config_.min_trip_pose_x_m < 0.0 || pose_x_m >= config_.min_trip_pose_x_m;
  const bool range_trip_candidate =
    std::isfinite(min_fwd) && min_fwd < static_cast<float>(config_.stop_distance);

  if (range_trip_candidate && pose_ok) {
    trip_confirm_count_++;
  } else if (!latched_stop_) {
    trip_confirm_count_ = 0;
  }

  if (!latched_stop_ && trip_confirm_count_ >= config_.trip_confirm_scans) {
    latched_stop_ = true;
    last_trip_range_m_ = static_cast<double>(min_fwd);
    latch_trip_time_sec_ = now_sec;
    release_clear_since_sec_ = -1.0;
    state_ = DriveState::Stopped;
    stop_reason_ = StopReason::Obstacle;
    return Twist2D{0.0, 0.0};
  }

  if (latched_stop_) {
    if (config_.latch_release_enable && std::isfinite(min_fwd) && min_fwd >= release_threshold) {
      if (release_clear_since_sec_ < 0.0) {
        release_clear_since_sec_ = now_sec;
      }
      const double clear_for = now_sec - release_clear_since_sec_;
      if (clear_for >= config_.release_dwell_sec) {
        latched_stop_ = false;
        latch_trip_time_sec_ = -1.0;
        release_clear_since_sec_ = -1.0;
        trip_confirm_count_ = 0;
        state_ = DriveState::Following;
        stop_reason_ = StopReason::None;
        return cmd;
      }
    } else {
      release_clear_since_sec_ = -1.0;
    }
    state_ = DriveState::Stopped;
    stop_reason_ = StopReason::Obstacle;
    return Twist2D{0.0, 0.0};
  }

  state_ = DriveState::Following;
  stop_reason_ = StopReason::None;
  return cmd;
}

}  // namespace grc_robot
