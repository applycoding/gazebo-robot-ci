// SPDX-License-Identifier: Apache-2.0

#include <cmath>
#include <limits>
#include <vector>

#include <gtest/gtest.h>

#include "grc_robot/safety_stop.hpp"

using grc_robot::DriveState;
using grc_robot::SafetyConfig;
using grc_robot::SafetyStop;
using grc_robot::ScanView;
using grc_robot::StopReason;
using grc_robot::Twist2D;

static ScanView make_forward_scan(float forward_range)
{
  ScanView s;
  s.angle_min = static_cast<float>(-M_PI);
  s.angle_increment = static_cast<float>(M_PI / 90.0);
  s.range_min = 0.08F;
  s.range_max = 10.0F;
  s.ranges.assign(181, std::numeric_limits<float>::infinity());
  s.ranges[90] = forward_range;
  return s;
}

TEST(SafetyStopTest, ObstacleTripsAt049)
{
  SafetyStop s(SafetyConfig{});
  const ScanView scan = make_forward_scan(0.49F);
  const Twist2D in{0.4, 0.0};
  const Twist2D out = s.overlay(in, &scan, 1.0, 1.0, true);
  EXPECT_NEAR(out.v, 0.0, 1e-6);
  EXPECT_EQ(s.stop_reason(), StopReason::Obstacle);
}

TEST(SafetyStopTest, ClearRangePasses)
{
  SafetyStop s(SafetyConfig{});
  const ScanView scan = make_forward_scan(2.0F);
  const Twist2D in{0.4, 0.0};
  const Twist2D out = s.overlay(in, &scan, 1.0, 1.0, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}

TEST(SafetyStopTest, AllInfHealthy)
{
  SafetyStop s(SafetyConfig{});
  ScanView scan = make_forward_scan(2.0F);
  for (float & r : scan.ranges) {
    r = std::numeric_limits<float>::infinity();
  }
  const Twist2D in{0.4, 0.0};
  const Twist2D out = s.overlay(in, &scan, 1.0, 1.0, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}

TEST(SafetyStopTest, SelfReturnIgnored)
{
  SafetyStop s(SafetyConfig{});
  const Twist2D in{0.4, 0.0};
  const ScanView near_self = make_forward_scan(0.05F);
  const Twist2D out = s.overlay(in, &near_self, 1.0, 1.0, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
  const ScanView obstacle = make_forward_scan(0.49F);
  const Twist2D tripped = s.overlay(in, &obstacle, 1.0, 1.0, true);
  EXPECT_NEAR(tripped.v, 0.0, 1e-6);
}

TEST(SafetyStopTest, Hysteresis)
{
  SafetyConfig cfg;
  cfg.latch_release_enable = true;
  SafetyStop s(cfg);
  const Twist2D in{0.4, 0.0};
  const ScanView trip = make_forward_scan(0.49F);
  (void)s.overlay(in, &trip, 1.0, 1.0, true);
  const ScanView hold = make_forward_scan(0.55F);
  Twist2D out = s.overlay(in, &hold, 1.1, 1.1, true);
  EXPECT_NEAR(out.v, 0.0, 1e-6);
  const ScanView release = make_forward_scan(0.60F);
  out = s.overlay(in, &release, 1.2, 1.2, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}

TEST(SafetyStopTest, ReleaseDwellResetsOnObscuredScan)
{
  SafetyConfig cfg;
  cfg.latch_release_enable = true;
  cfg.release_dwell_sec = 1.0;
  SafetyStop s(cfg);
  const Twist2D in{0.4, 0.0};
  const ScanView trip = make_forward_scan(0.49F);
  const ScanView clear_a = make_forward_scan(0.65F);
  const ScanView obscured = make_forward_scan(0.55F);
  (void)s.overlay(in, &trip, 1.0, 1.0, true);
  (void)s.overlay(in, &clear_a, 1.5, 1.5, true);
  Twist2D out = s.overlay(in, &obscured, 1.8, 1.8, true);
  EXPECT_NEAR(out.v, 0.0, 1e-6);
  out = s.overlay(in, &clear_a, 2.0, 2.0, true);
  EXPECT_NEAR(out.v, 0.0, 1e-6);
  out = s.overlay(in, &clear_a, 3.1, 3.1, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}

TEST(SafetyStopTest, NanIgnored)
{
  SafetyStop s(SafetyConfig{});
  ScanView scan = make_forward_scan(2.0F);
  scan.ranges[90] = std::numeric_limits<float>::quiet_NaN();
  const Twist2D in{0.4, 0.0};
  const Twist2D out = s.overlay(in, &scan, 1.0, 1.0, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}

TEST(SafetyStopTest, ScanTimeout)
{
  SafetyConfig cfg;
  cfg.require_scan = true;
  SafetyStop s(cfg);
  const Twist2D in{0.4, 0.0};
  (void)s.overlay(in, nullptr, 0.0, -1.0, true);
  const Twist2D out = s.overlay(in, nullptr, 2.0, -1.0, true);
  EXPECT_NEAR(out.v, 0.0, 1e-6);
  EXPECT_EQ(s.state(), DriveState::ScanTimeout);
}

TEST(SafetyStopTest, RequireScanFalse)
{
  SafetyConfig cfg;
  cfg.require_scan = false;
  SafetyStop s(cfg);
  const Twist2D in{0.4, 0.0};
  const Twist2D out = s.overlay(in, nullptr, 2.0, -1.0, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}

TEST(SafetyStopTest, LatchHoldsWithoutReleaseEnable)
{
  SafetyStop s(SafetyConfig{});
  const Twist2D in{0.4, 0.0};
  const ScanView trip = make_forward_scan(0.49F);
  (void)s.overlay(in, &trip, 1.0, 1.0, true);
  const ScanView release = make_forward_scan(2.0F);
  const Twist2D out = s.overlay(in, &release, 1.2, 1.2, true);
  EXPECT_NEAR(out.v, 0.0, 1e-6);
}

TEST(SafetyStopTest, EnableFalse)
{
  SafetyConfig cfg;
  cfg.enable = false;
  SafetyStop s(cfg);
  const Twist2D in{0.4, 0.0};
  const ScanView near = make_forward_scan(0.30F);
  const Twist2D out = s.overlay(in, &near, 1.0, 1.0, true);
  EXPECT_NEAR(out.v, 0.4, 1e-6);
}
