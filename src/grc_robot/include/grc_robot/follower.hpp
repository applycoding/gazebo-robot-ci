// SPDX-License-Identifier: Apache-2.0
// gazebo-robot-ci — Arpan Bom

#ifndef GRC_ROBOT__FOLLOWER_HPP_
#define GRC_ROBOT__FOLLOWER_HPP_

#include <cstddef>
#include <vector>

#include "grc_robot/types.hpp"

namespace grc_robot
{

class Follower
{
public:
  Follower();
  explicit Follower(FollowerConfig config);

  [[nodiscard]] Twist2D step(
    const Pose2D & pose,
    const std::vector<Pose2D> & path,
    std::size_t & index,
    double dt) const;

  [[nodiscard]] DriveState state() const { return state_; }

  void reset();

private:
  static double wrap_yaw(double yaw);

  FollowerConfig config_;
  mutable DriveState state_{DriveState::Idle};
};

}  // namespace grc_robot

#endif  // GRC_ROBOT__FOLLOWER_HPP_
