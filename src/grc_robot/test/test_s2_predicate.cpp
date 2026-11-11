// SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>
#include <string>

namespace
{
bool s2_pass_predicate(const char * reason, const char * observed, double trip_range_m)
{
  if (reason != nullptr && std::string(reason) == "scan_timeout") {
    return false;
  }
  if (observed != nullptr && std::string(observed) == "scan_timeout") {
    return false;
  }
  if (trip_range_m < 0) {
    return false;
  }
  if (trip_range_m >= 0.50) {
    return false;
  }
  return true;
}
}  // namespace

TEST(S2PredicateTest, TimeoutStopDoesNotPass)
{
  EXPECT_FALSE(s2_pass_predicate("scan_timeout", "scan_timeout", -1.0));
}
