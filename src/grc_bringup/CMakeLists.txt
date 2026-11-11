# SPDX-License-Identifier: Apache-2.0
cmake_minimum_required(VERSION 3.22)
project(grc_bringup)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

install(DIRECTORY launch worlds config DESTINATION share/${PROJECT_NAME})
install(PROGRAMS
  script/write_report.py
  script/write_badge.py
  script/publish_waypoints.py
  script/run_scenario_test.py
  script/publish_zero_cmd.py
  script/run_scenario_launch_test.sh
  script/collect_gz_contact_debug.sh
  script/contact_relay.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_python_install_package(${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(
    test_scenarios
    test/test_scenarios.py
    TIMEOUT 600
    ENV GRC_ARTIFACTS_DIR=/ws/artifacts
  )
endif()

ament_package()
