// SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>
#include <vector>

#include "grc_robot/follower.hpp"

using grc_robot::DriveState;
using grc_robot::Follower;
using grc_robot::FollowerConfig;
using grc_robot::Pose2D;
using grc_robot::Twist2D;

TEST(FollowerTest, AlreadyAtGoal)
{
  FollowerConfig cfg;
  Follower f(cfg);
  std::vector<Pose2D> path{{0.0, 0.0, 0.0}};
  std::size_t idx = 0;
  const Pose2D pose{0.0, 0.0, 0.0};
  const Twist2D cmd = f.step(pose, path, idx, 0.02);
  EXPECT_NEAR(cmd.v, 0.0, 1e-6);
  EXPECT_NEAR(cmd.omega, 0.0, 1e-6);
  EXPECT_EQ(f.state(), DriveState::Arrived);
}

TEST(FollowerTest, CruiseToward2m)
{
  FollowerConfig cfg;
  Follower f(cfg);
  std::vector<Pose2D> path{{2.0, 0.0, 0.0}};
  std::size_t idx = 0;
  const Twist2D cmd = f.step(Pose2D{0, 0, 0}, path, idx, 0.02);
  EXPECT_NEAR(cmd.v, 0.40, 0.02);
  EXPECT_LE(std::abs(cmd.omega), 0.05);
}

TEST(FollowerTest, TurnLeft90)
{
  FollowerConfig cfg;
  Follower f(cfg);
  std::vector<Pose2D> path{{0.0, 2.0, 0.0}};
  std::size_t idx = 0;
  const Twist2D cmd = f.step(Pose2D{0, 0, 0}, path, idx, 0.02);
  EXPECT_GT(cmd.omega, 0.0);
  EXPECT_LE(std::abs(cmd.omega), 1.20);
  EXPECT_LE(std::abs(cmd.v), 0.50);
}

TEST(FollowerTest, LastWaypointYawOnly)
{
  FollowerConfig cfg;
  Follower f(cfg);
  std::vector<Pose2D> path{{1.0, 0.0, 1.0}};
  std::size_t idx = 0;
  Pose2D pose{0.95, 0.0, 0.0};
  Twist2D cmd = f.step(pose, path, idx, 0.02);
  EXPECT_NEAR(cmd.v, 0.0, 1e-6);
  EXPECT_NE(cmd.omega, 0.0);
}

TEST(FollowerTest, TwoWaypoints)
{
  FollowerConfig cfg;
  Follower f(cfg);
  std::vector<Pose2D> path{{1.0, 0.0, 0.0}, {2.0, 0.0, 0.0}};
  std::size_t idx = 0;
  Pose2D pose{0.95, 0.0, 0.0};
  (void)f.step(pose, path, idx, 0.02);
  EXPECT_EQ(idx, 1u);
  pose = {1.95, 0.0, 0.0};
  const Twist2D cmd = f.step(pose, path, idx, 0.02);
  EXPECT_EQ(f.state(), DriveState::Arrived);
  EXPECT_NEAR(cmd.v, 0.0, 1e-6);
}
