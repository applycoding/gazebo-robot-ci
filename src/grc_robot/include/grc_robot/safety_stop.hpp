// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci - Arpan Bom

#ifndef GRC_ROBOT__SAFETY_STOP_HPP_
#define GRC_ROBOT__SAFETY_STOP_HPP_

#include <cstdint>
#include <vector>

#include "grc_robot/types.hpp"

namespace grc_robot
{

struct ScanView
{
  std::vector<float> ranges;
  float angle_min{0.0F};
  float angle_increment{0.0F};
  float range_min{0.08F};
  float range_max{10.0F};
};

class SafetyStop
{
public:
  SafetyStop();
  explicit SafetyStop(SafetyConfig config);

  Twist2D overlay(
    const Twist2D & cmd,
    const ScanView * scan,
    double now_sec,
    double last_valid_scan_stamp_sec,
    bool commanding,
    double pose_x_m = -1.0);

  [[nodiscard]] DriveState state() const { return state_; }
  [[nodiscard]] StopReason stop_reason() const { return stop_reason_; }
  [[nodiscard]] bool latched_stop() const { return latched_stop_; }
  [[nodiscard]] double last_trip_range_m() const { return last_trip_range_m_; }

  void reset();

private:
  [[nodiscard]] bool scan_is_valid(const ScanView & scan) const;
  [[nodiscard]] float min_forward_finite_range(const ScanView & scan) const;

  SafetyConfig config_;
  DriveState state_{DriveState::Idle};
  StopReason stop_reason_{StopReason::None};
  bool latched_stop_{false};
  double last_trip_range_m_{-1.0};
  double latch_trip_time_sec_{-1.0};
  double release_clear_since_sec_{-1.0};
  bool first_command_time_set_{false};
  double first_command_time_sec_{0.0};
  int trip_confirm_count_{0};
};

}  // namespace grc_robot

#endif  // GRC_ROBOT__SAFETY_STOP_HPP_
