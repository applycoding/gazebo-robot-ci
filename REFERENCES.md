# References

Permissively licensed GitHub projects used as **references only**, except `ros_gz` and the Gazebo Jetty libraries which are also **apt dependencies** (not vendored or copied by hand). Do not copy tutorial worlds, launch files, or robot models. Credit any conceptually derived idea in the README. Licenses were checked on 2026-11-10 with `gh api repos/OWNER/REPO --jq .license.spdx_id` and with package.xml or LICENSE files when needed.

**Outbound license for this demo repo is Apache-2.0**, not MIT. A LICENSE file with the official Apache-2.0 text, a NOTICE file crediting Arpan Bom, and SPDX-License-Identifier: Apache-2.0 headers are required at build time.

This demo must not duplicate existing applycoding repos:

| Repo | What it already is | How this demo differs |
| --- | --- | --- |
| [applycoding/ros2-nav2-slam-sim](https://github.com/applycoding/ros2-nav2-slam-sim) | Humble, Gazebo Classic (`gazebo_ros`), slam_toolbox, Nav2, office world, YAML `NavigateToPose` runner. README: nothing there starts Gazebo in CI. | Modern `gz sim` **does** run headless in GitHub Actions. No Nav2, SLAM, AMCL, or office mission. Focus is the test/CI harness around a small custom C++ node. Do not copy that repo (MIT outbound). |
| [applycoding/ros2-voice-command-robot](https://github.com/applycoding/ros2-voice-command-robot) | Voice + Nav2 demo; CI uses `ros:humble-ros-base` with mock backends | This repo runs real headless Gazebo in Actions. |
| [applycoding/rosbag-eval-bench](https://github.com/applycoding/rosbag-eval-bench) | Offline MCAP metric regression | Online node under test in `gz sim`, not bag replay. |
| [applycoding/nav2-coverage-planner-compare](https://github.com/applycoding/nav2-coverage-planner-compare) / [teb-mpc-local-planner](https://github.com/applycoding/teb-mpc-local-planner) / [nav2-behavior-trees](https://github.com/applycoding/nav2-behavior-trees) | Planner and behavior-tree demos | Not a Gazebo CI framework. |
| [applycoding/teleop-console-demo](https://github.com/applycoding/teleop-console-demo) | Human teleop of a diff-drive robot | Automated sim tests, not teleop. |

## Selected references (7)

### 1. gazebosim/ros_gz

- URL: https://github.com/gazebosim/ros_gz
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0; `package.xml` on the `lyrical` branch says Apache 2.0)
- Docs: https://docs.ros.org/en/lyrical/p/ros_gz_sim/ and https://docs.ros.org/en/lyrical/p/ros_gz_bridge/ (both 3.0.12, 2026-10-22)
- This is an **apt dependency** as well as a reference (`ros-lyrical-ros-gz` 3.0.12 and the sim, bridge, and interfaces packages). Use the distro binaries. Do not vendor the source. Bridge type table (lyrical README): `sensor_msgs/msg/LaserScan` ↔ `gz.msgs.LaserScan`, `ros_gz_interfaces/msg/Contacts` ↔ `gz.msgs.Contacts`.

### 2. gazebosim/gz-sim

- URL: https://github.com/gazebosim/gz-sim
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0)
- Branch / API: `gz-sim10` (Jetty). Docs: https://gazebosim.org/docs/jetty/ , releases https://gazebosim.org/docs/latest/releases/ (Jetty LTS, EOL May 2031)
- Borrow: CPU lidar (`examples/worlds/cpu_lidar_sensor.sdf`, plugin `gz-sim-cpu-lidar-system`), DiffDrive (`examples/worlds/diff_drive.sdf`, `gz-sim-diff-drive-system`, https://gazebosim.org/api/sim/10/classgz_1_1sim_1_1systems_1_1DiffDrive.html), contact system (`examples/worlds/contact_sensor.sdf`). Official pairing with ROS 2 Lyrical: https://gazebosim.org/docs/latest/ros_installation/ . Do **not** copy example worlds wholesale. Headless-rendering tutorial (https://gazebosim.org/api/sim/10/headless_rendering.html) is recovery-path only; v1 default does not use a render engine.

### 3. ros2/launch (`launch_testing`, `launch_testing_ament_cmake`)

- URL: https://github.com/ros2/launch
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0)
- Docs: https://docs.ros.org/en/lyrical/p/launch_testing/ and https://docs.ros.org/en/lyrical/p/launch_testing_ament_cmake/
- Borrow: the idea of a launch description plus post-start tests. Use the Lyrical apt packages. Do not copy tests from other robots.

### 4. ros2/launch_ros (`launch_testing_ros`)

- URL: https://github.com/ros2/launch_ros
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0)
- Docs: https://docs.ros.org/en/lyrical/p/launch_testing_ros/
- Borrow: ROS-aware launch_testing helpers. Distro packages only.

### 5. ros2/examples

- URL: https://github.com/ros2/examples
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0)
- Borrow: the *shape* of a small C++ publisher/subscriber node. Do not copy sources.

### 6. gazebosim/sdformat

- URL: https://github.com/gazebosim/sdformat
- License: **Apache-2.0** (`gh api` SPDX: Apache-2.0)
- Spec: http://sdformat.org/spec?ver=1.12&elem=sensor
- Borrow: sensor and collision SDF *ideas* for the in-tree model. Write a new minimal robot; do not copy example models.

### 7. google/googletest

- URL: https://github.com/google/googletest
- License: **BSD-3-Clause** (`gh api` SPDX: BSD-3-Clause)
- Upstream v1.18.0 is context only. This demo uses the **ament / distro** provider in the Lyrical image, not a FetchContent pin. NOTICE records the installed package name and version.

## Idea-only or exclude

- ros-controls/gz_ros2_control — Apache-2.0. Idea-only. v1 uses stock `gz-sim-diff-drive-system`, not ros2_control.
- ros-navigation/navigation2 — mixed licenses; not a dependency. This demo is not a Nav2 stack and must not vendor or copy it.
- TurtleBot / turtlebot3 / turtlebot4 models — do not copy.
- applycoding/ros2-nav2-slam-sim — MIT, different stack (Classic + Nav2 + SLAM). Do not copy worlds, descriptions, or prose.
- GPL or LGPL simulators, planners, or plugins — not dependencies.
