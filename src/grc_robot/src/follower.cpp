// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci — Arpan Bom

#include "grc_robot/follower.hpp"

#include <algorithm>
#include <cmath>

namespace grc_robot
{

Follower::Follower()
: Follower(FollowerConfig{})
{
}

Follower::Follower(FollowerConfig config)
: config_(config)
{
}

double Follower::wrap_yaw(double yaw)
{
  while (yaw > M_PI) {
    yaw -= 2.0 * M_PI;
  }
  while (yaw <= -M_PI) {
    yaw += 2.0 * M_PI;
  }
  return yaw;
}

void Follower::reset()
{
  state_ = DriveState::Idle;
}

Twist2D Follower::step(
  const Pose2D & pose,
  const std::vector<Pose2D> & path,
  std::size_t & index,
  double /*dt*/) const
{
  Twist2D out{0.0, 0.0};
  if (path.empty()) {
    state_ = DriveState::Idle;
    return out;
  }

  index = std::min(index, path.size() - 1);
  const Pose2D & target = path[index];
  const double dx = target.x - pose.x;
  const double dy = target.y - pose.y;
  const double dist_xy = std::hypot(dx, dy);
  const bool is_last = (index + 1 >= path.size());
  const double yaw_err = wrap_yaw(target.yaw - pose.yaw);

  if (dist_xy <= config_.goal_tol_xy) {
    if (is_last) {
      if (std::abs(yaw_err) <= config_.goal_tol_yaw) {
        state_ = DriveState::Arrived;
        return out;
      }
      out.v = 0.0;
      out.omega = std::clamp(yaw_err * config_.heading_kp, -config_.omega_max, config_.omega_max);
      state_ = DriveState::Following;
      return out;
    }
    index += 1;
    return step(pose, path, index, 0.0);
  }

  const double heading_to_wp = std::atan2(dy, dx);
  double steer_err = wrap_yaw(heading_to_wp - pose.yaw);
  double v = config_.v_cruise;
  if (v > config_.v_max) {
    v = config_.v_max;
  }
  double omega = steer_err * config_.heading_kp;
  omega = std::clamp(omega, -config_.omega_max, config_.omega_max);

  out.v = v;
  out.omega = omega;
  state_ = DriveState::Following;
  return out;
}

}  // namespace grc_robot
