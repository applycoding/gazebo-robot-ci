# SPDX-License-Identifier: Apache-2.0
cmake_minimum_required(VERSION 3.22)
project(grc_robot)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake_auto REQUIRED)
ament_auto_find_build_dependencies()

ament_auto_add_library(grc_robot_lib
  src/follower.cpp
  src/safety_stop.cpp
  src/waypoint_follower_node.cpp
)
target_include_directories(grc_robot_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_auto_add_executable(grc_waypoint_follower src/waypoint_follower_main.cpp)
target_link_libraries(grc_waypoint_follower grc_robot_lib)

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY models/ DESTINATION share/${PROJECT_NAME}/models)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_follower test/test_follower.cpp)
  target_link_libraries(test_follower grc_robot_lib)
  ament_add_gtest(test_safety test/test_safety.cpp)
  target_link_libraries(test_safety grc_robot_lib)
  ament_add_gtest(test_node test/test_node.cpp)
  target_link_libraries(test_node grc_robot_lib)
  ament_add_gtest(test_s2_predicate test/test_s2_predicate.cpp)
  target_link_libraries(test_s2_predicate grc_robot_lib)
endif()

ament_auto_package()
