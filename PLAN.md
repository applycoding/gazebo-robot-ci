# gazebo-robot-ci - v1 plan

Revised 2026-11-10 after independent review and independent version, URL, license, geometry, and CI checks. Outbound license is **Apache-2.0**. Planning only; this document does not create a public repo or implementation.

## Goal

Public portfolio demo for Arpan Bom: a repeatable **headless Gazebo CI harness** around one small C++ ROS 2 node. A push to `main` runs, inside a digest-pinned official ROS container on an `ubuntu-26.04` runner:

1. gtest of a waypoint follower and a safety-stop overlay, with Gazebo never started.
2. Headless Gazebo Jetty `launch_testing` scenarios that check: reaches a goal in time, stops before an obstacle, and does not collide; plus a mutant that must collide and a brake-only run that must miss the goal.
3. `artifacts/ci-report.json` (schema version 1), a Markdown twin, gcovr HTML + Cobertura, and a static badge SVG.
4. A Vite dashboard at GitHub Pages base `/gazebo-robot-ci/` that loads that JSON. The page cannot run Gazebo. It is labelled simulation-only and **recorded CI output**.

Lely's listing names Gazebo, automated tests, and CI, and 13 tracked roles ask for CI or automated testing. This repo does not claim Lely production HIL, a certified robot-test lab, Nav2, or SLAM CI.

Git author and committer: **Arpan Bom <applycoding@gmail.com>**. No `Co-authored-by` trailer. No credit to any assistant or tool in the README, NOTICE, or commits.

`gh repo list applycoding --limit 200` on 2026-11-10 shows no `applycoding/gazebo-robot-ci`.

## Scope

Two ament packages (`grc_robot`, `grc_bringup`), one in-tree primitive SDF robot, two worlds, ros_gz bridge config, launch_testing, a report writer, a coverage floor on the core C++ library, **one** GitHub Actions workflow, and a Pages app.

Differentiate existing applycoding repos (same `gh repo list` check):

- **applycoding/ros2-nav2-slam-sim** (closest): ROS 2 Humble, **Gazebo Classic** (`gazebo_ros`), slam_toolbox, Nav2 `NavigateToPose`, office world. Its README states that nothing there starts Gazebo in CI. This repo is the opposite focus: a **test and CI framework** that **does** run headless modern `gz sim` on GitHub Actions. No SLAM, AMCL, Nav2, map_server, or multi-room mission. Do not depend on, submodule, vendor, or copy that repo (MIT outbound; this repo is Apache-2.0). Comparative README claims must link that repository's README at a fixed commit.
- applycoding/ros2-voice-command-robot: ROS 2 + Gazebo voice/Nav2 demo; CI colcon-builds in `ros:humble-ros-base` and runs pytest with mock backends; it does not run Gazebo in Actions.
- applycoding/rosbag-eval-bench: offline MCAP metric regression, no Gazebo.
- applycoding/nav2-coverage-planner-compare, teb-mpc-local-planner, nav2-behavior-trees, ekf-gnss-localization, sim-gimbal-stabilizer: planners, trees, and estimators, not a Gazebo CI harness.
- applycoding/teleop-console-demo: human teleop.
- applycoding/lidar-shape-classifier-ros2, ros2-vision-tracking-demo, ros2-drone-mission-sim: other ROS 2 demos, no Gazebo CI dashboard.

Reimplement a minimal robot and worlds. Do not copy TurtleBot models or that office world.

## Architecture

**Decision: ROS 2 Lyrical Luth + Gazebo Jetty on Ubuntu Resolute 26.04.** Official Gazebo install docs (https://gazebosim.org/docs/latest/ros_installation/, HTTP 200, last-modified 2026-11-10) recommend that pair for new work. The compatibility table marks Lyrical + Jetty ✅, Jazzy + Harmonic ✅ (previous LTS), Humble + Fortress ✅. Lyrical vendor packages contain Jetty; Jazzy contains Harmonic. Do not mix Lyrical with Harmonic or Jazzy with Jetty. Do not use Gazebo Classic or unofficial `packages.osrfoundation.org` pairings. Humble + Fortress would retread ros2-nav2-slam-sim. Kilted + Ionic is not an LTS pair (Ionic EOL 2026-12). Install with `apt-get install ros-lyrical-ros-gz` from packages.ros.org. Lyrical `ros_gz` is **3.0.12** (package.xml on the `lyrical` branch, docs.ros.org `ros_gz_sim` / `ros_gz_bridge` 3.0.12 dated 2026-10-22, and the Resolute pool file `ros-lyrical-ros-gz_3.0.12-1resolute.deb`). **Last resort only:** if a pin or a test proves official `ros-lyrical-ros-gz` cannot be installed, or headless Jetty cannot be made green on GitHub-hosted runners, record the failure log and switch the same tests to Jazzy + Harmonic without changing the node API.

**Decision: CI invokes `docker run`, not a GHA `container:` job.** Host is `runs-on: ubuntu-26.04` (GA 2026-09-17; https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/). Never `ubuntu-latest` (that label is mid-migration from 24.04 to 26.04 between 2026-10-19 and 2026-11-19). Record the runner image version (`ImageOS` / `ImageVersion`) in the report. Image: official Docker Library `ros:lyrical-ros-base@sha256:3224ee150cb02eb89a5e0811bc267b57ed3a91b9c10191df57810726a7e916d7` (multi-arch index `docker-content-digest` of tag `lyrical-ros-base`, queried from registry-1.docker.io on 2026-11-10). linux/amd64 manifest: `sha256:4e129b13f5c72d1630b03513af404353b44b30c793fd6d99b362f29ca7a15f50`. Both digests go in `.github/workflow-pins.md` and in workflow comments. Pull with `--platform linux/amd64`. Re-check at first CI write; keep these plan-time digests unless a digest pull 404s, and bump only with a recorded digest change. Do not float the tag.

Command shape: `docker run --rm --init --platform linux/amd64 -v "$GITHUB_WORKSPACE:/ws" -w /ws --shm-size=1g -e DISPLAY= -e LIBGL_ALWAYS_SOFTWARE=1`. Source `/opt/ros/lyrical/setup.bash` and the workspace overlay inside the container. Do not pass the host `DISPLAY`. Add `--security-opt seccomp=unconfined` only if a failing run shows seccomp breaks gz, and document why. Do not use `--privileged` unless a failing run proves it. `docker run` is a project choice for predictable `/dev/shm` and a simple in-container `apt-get`; a GHA `container:` job can also set `options: --shm-size=1g`, but v1 stays on `docker run`. The image is ros-base (colcon is present). CI then installs the ros-gz packages listed under Pinned stack, plus build, test, Mesa (only as a recovery path), and a Python venv for gcovr. Pin apt versions at the first green run in `apt-pins.txt`, starting from `ros-lyrical-ros-gz=3.0.12-1resolute` (exact revision confirmed with `apt-cache policy` in that run). A digest-pinned **base** image does not freeze apt: `apt-get update` can still move transitives. v1 does **not** publish a derived image. Accept bounded apt drift, pin the metapackage and other direct packages once recorded, and upload the apt resolution log as an artifact. Container Python is Ubuntu Resolute's **3.14** (`python3` 3.14.3-0ubuntu2 on packages.ubuntu.com, 2026-11-10). Compile with the image cmake. Package `cmake_minimum_required` is 3.22. Host CMake on the runner is irrelevant.

**Decision: CPU lidar and a contact oracle, no render engine in the default path.** Jetty / gz-sim 10 ships a physics-based lidar that raycasts with DART + Bullet and does not need a GPU or OGRE (official example `examples/worlds/cpu_lidar_sensor.sdf` on branch `gz-sim10`: plugin `gz-sim-cpu-lidar-system` / `gz::sim::systems::CpuLidar`; “not the sensors system”). Locked server command: `DISPLAY= gz sim -s -r <world.sdf>` (server only, run immediately, no GUI, no `--headless-rendering`). Worlds must:

- Use `<physics name="1ms" type="dart">` with `<max_step_size>0.001</max_step_size>`, requested `<real_time_factor>1.0</real_time_factor>`, and `<dart><collision_detector>bullet</collision_detector></dart>` (other DART detectors do not support this raycast).
- Load `gz-sim-physics-system`, `gz-sim-cpu-lidar-system`, and `gz-sim-contact-system` (`gz::sim::systems::Contact`). Do **not** load the GPU sensors system in shipped worlds.
- Contain no cameras and no Fuel URIs.

`--headless-rendering` and Mesa EGL (`libegl1`, `libegl-mesa0`, `libgl1`, `libgl1-mesa-dri` 26.0.3-1ubuntu1, `libglx-mesa0`, `libgbm1`, `libgles2`, `LIBGL_ALWAYS_SOFTWARE=1`) are a **recovery path only**, if a later change reintroduces a render sensor. They are not required for the CPU-lidar default. `/dev/shm` is 1g. Sim-job `timeout-minutes: 40`; unit job 15; web job 15. S1 simulated duration ≤ 20 s; S2 ≤ 15 s. Wall-clock is not a golden gate. Every readiness wait and process has a wall-time watchdog; a frozen `/clock` fails the test. Upload logs with `if: always()`. Do not drop the mutant or brake-only tests to make CI green. Requested RTF 1.0 is not a guaranteed achieved RTF; if measured throughput on a hosted runner cannot finish the suite inside 40 minutes, first reduce lidar sample count (not below 31) and reuse the pulled image / apt cache, then record evidence. Do not silently skip scenarios.

**Decision: one node, parameter mutant, stock DiffDrive plant, one in-tree SDF.** `grc_waypoint_follower` is one `rclcpp` process. `safety_stop.enable` defaults true and **only** disables the obstacle-range overlay when false. The missing-scan fail-safe stays on in all sim runs (`safety_stop.require_scan` is true). The mutant is that parameter set false, not a second source tree. **No ros2_control and no xacro in v1.** One installed SDF model, included by both worlds, primitive shapes only (cylinder body, two wheel cylinders, a ball caster under the body, a small lidar housing). No URDF/xacro alternative.

Kinematics live in Jetty `gz::sim::systems::DiffDrive`, `filename="gz-sim-diff-drive-system"` (API: https://gazebosim.org/api/sim/10/classgz_1_1sim_1_1systems_1_1DiffDrive.html; example `examples/worlds/diff_drive.sdf` on `gz-sim10`). Locked plugin fields: `left_joint` / `right_joint`, `wheel_separation` 0.26 m, `wheel_radius` **0.05 m**, `max_linear_velocity` 0.50, `min_linear_velocity` -0.50, `max_linear_acceleration` 1.0, `min_linear_acceleration` -1.0, `max_angular_velocity` 1.20, `min_angular_velocity` -1.20, `max_angular_acceleration` 2.0, `min_angular_acceleration` -2.0, `<topic>/cmd_vel</topic>`, `<odom_topic>/odom</odom_topic>`, `<frame_id>odom</frame_id>`, `<child_frame_id>base_link</child_frame_id>`. Default gz odometry is model-scoped; the explicit topics above are required so the ROS bridge can use `/cmd_vel` and `/odom`. Plugin command limits are not a proof of physical braking; S2 measures stopped speed from odometry.

Controller: hold a `nav_msgs/Path` in frame `odom` (v1 has no separate `map` frame; `world`, the ground plane, and `odom` coincide at spawn and stay that way because there is no localization). Cruise `v` toward the current waypoint with heading P gain `heading_kp = 1.5`, clamp to `v_max` and `ω_max`, wrap yaw error to (-π, π], positive yaw error (target to the left) yields positive ω. Advance when `hypot(dx,dy) <= goal_tol_xy`. On the **last** pose, once xy is inside tolerance, command **v = 0** and rotate in place toward the goal yaw until `goal_tol_yaw`, then publish `(0,0)` and state `arrived`. A heading toward an already-reached last waypoint must not keep a non-zero linear command that fights final yaw.

Safety overlay: any **finite** LaserScan range that is inside `[range_min, range_max]` and inside ±`forward_half_angle_rad` (**0.262 rad, ±15°**) and is below `stop_distance` **0.50 m** forces `(0,0)` and state `stopped`. Release only when min forward finite range ≥ `stop_distance + stop_release_margin` with margin **0.10 m** (0.60 m). NaN, Inf, values outside `[range_min, range_max]`, and beams outside the window are ignored for the min. An all-`+Inf` scan is a **healthy empty-space scan**, not a missing scan, and must not trip S1. An empty `ranges` array or an all-NaN scan is invalid and does not update the min. If `safety_stop.require_scan` is true (default in sim) and no **fresh valid** scan arrives within `scan_timeout` **0.5 s** after the node has started commanding, command `(0,0)` and state `scan_timeout`. Fresh means the scan stamp is within 0.5 s of sim now. `safety_stop.require_scan:=false` is gtest-only and is never used by sim scenarios. This is a teaching follower, not a Nav2 controller and not a certified safety function. The missing-scan policy is a demo fail-safe, not ISO 13849 / ISO 26262.

**Decision: geometry, lidar placement, and hand-checkable S2 numbers.** Circular body `robot_radius_m = 0.15`. Body is a cylinder of radius 0.15 m and height **0.20 m**, axis along z, bottom at z = 0.05 m (above the wheel-ground contact) and top at z = 0.25 m. Wheel track 0.26 m, wheel radius 0.05 m, caster under the body (inside the disk). `v_cruise = 0.40`, `v_max = 0.50`, `ω_max = 1.20` rad/s, `goal_tol_xy = 0.20` m, `goal_tol_yaw = 0.30` rad. Frames: `odom` / `world` ENU, `base_link`, `laser_link` at **x = +0.12 m, y = 0, z = 0.27 m** in `base_link` (2 cm above the body top). Horizontal CPU-lidar rays therefore do not intersect the body collision, but still intersect the S2 box (box top is z = 0.40 m). All sim tests set `use_sim_time:=true`.

CPU lidar (sensor `type="lidar"`, processed by the CpuLidar system): topic `/scan`, `update_rate` **10**, `always_on` 1, `visualize` false, 181 horizontal samples from -π to +π (includes a zero-angle ray), 1 vertical sample at 0, `range.min` **0.08**, `range.max` **10.0**, `range.resolution` 0.01, noise off, frame `laser_link`. The ±0.262 rad safety window is a selection within that FOV.

S2 box: axis-aligned cube **0.40 m**, center **(2.0, 0.0, 0.20)**, near face the plane **x = 1.80**. With the laser at x_link = +0.12, forward range to that face is `r = 1.80 - (x + 0.12) = 1.68 - x`. The overlay trips when `r < 0.50`, i.e. **`x > 1.18` m**. The disk touches the face when `x + 0.15 ≥ 1.80`, i.e. **`x ≥ 1.65` m**. Ideal coast at 0.40 m/s and 1.0 m/s² is `v²/2a = 0.08 m`, so the ideal settled pose is **x ≈ 1.26 m** (not 1.20). Body-to-face clearance there is 0.39 m; distance to box center is 0.74 m. Those are different metrics. Do not move the box or cut `v_cruise` to make the mutant miss.

Clearance is **circle-to-AABB**, not a radial distance to the box center. With box half-extents 0.20 m: `dx = max(abs(x-2.0)-0.20, 0)`, `dy = max(abs(y)-0.20, 0)`, `clearance = hypot(dx, dy) - 0.15`. Collision / penetration is `clearance < 0`. Report `min_clearance_m` as the minimum of that quantity over the run (and over wheel collision extents if a wheel ever leaves the 0.15 m disk; v1 wheels stay inside it). A centerline `hypot` to (2,0) is **not** the gate.

**Decision: reports and Pages consume CI output; they do not simulate.** Schema version **1**. A field or metric change bumps `report_version`. Exactly **four** rows, no alternatives: `s1`, `s2`, `s2_mutant_expects_contact`, `s1_brake_expects_miss`. For the two negatives, `pass: true` means the **test expectation succeeded** (the mutant produced a robot-box contact, or a healthy brake-only run missed the goal at 20 s sim). Infrastructure failure, missing telemetry, `scan_timeout`, a crash, or not reaching T_max must not count as the expected miss or contact. Badge text: `4/4 expectations passed` or `N/4 expectations passed`. README points at `/gazebo-robot-ci/badge.svg`. No third-party badge host. **One workflow** (`ci.yml`) contains `unit`, `sim`, `web`, and `pages` jobs. `pages` deploys the **tested** `web/dist` of a `main` push SHA only after `unit`, `sim`, and `web` of that SHA succeed. No `pages.yml`. No `pull_request_target`. Playwright checks the built dist after the report and badge have been copied in. CI uploads `docs/demo.png` as an artifact and does not commit it. Check the screenshot in locally once, labelled as a recorded example. `web/public/sample-report.json` is a real local or CI report with `sample: true`. The deployed report must have `sample: false`; the app must not silently fall back to the sample on `main`.

**Decision: gtest uses distro GoogleTest only.** `ament_cmake_gtest` from the Lyrical image. Record the actual provider (`libgtest-dev`, `gtest_vendor`, or whatever ament resolves) and its version at the first green run. Do not FetchContent. Upstream v1.18.0 (2026-08-10) is context, not a pin. Unit binaries do not link `gz` or `ros_gz`.

**Decision: coverage is gcov + gcovr 8.8 on the core library.** Pin **gcovr 8.8** (PyPI, BSD-3-Clause, `requires_python >= 3.10`, classifiers include 3.14; wheel sha256 `a5c3e3d4a9c8ab4a95aa8e4b072fcaec7962b1d9fb2add3f10645f649ef29545`, sdist sha256 `0320230a432c033c1a41f34ba943082f450008c789bee05d414e532f380fd788`). Install into a venv, not by overwriting the system Python. Hash-pin in `requirements-ci.txt`. Do not silently select another version. Run from `/ws` with `--root /ws`, search `build/grc_robot`, filter authored `src/grc_robot/src/follower.cpp`, `src/grc_robot/src/safety_stop.cpp`, and the matching headers; exclude tests, the node TU, installed copies, and generated code. The 80% line floor applies to **that core-library set only**, and is labelled as such. `waypoint_follower_node.cpp` is exercised by a thin gtest that constructs the ROS node (or its callback wrapper) without starting gz, plus the sim tests; it is not in the 80% denominator. Use `--fail-under-line 80`, compile **and** link with `--coverage`, require a nonzero measured line count, and upload the full HTML-details directory plus Cobertura XML. The job does not fail on bringup launch files.

## Pinned stack

Verified 2026-11-10 unless noted.

| Piece | Pin |
| --- | --- |
| ROS / OS | Lyrical Luth, Ubuntu Resolute 26.04. https://docs.ros.org/en/lyrical/ and https://docs.ros.org/en/lyrical/Get-Started/Installation/Ubuntu-Install-Debs.html (HTTP 200). Release note: https://docs.ros.org/en/rolling/Releases/Release-Lyrical-Luth.html |
| Gazebo | Jetty, gz-sim 10, EOL May 2031. https://gazebosim.org/docs/jetty/ , https://gazebosim.org/docs/latest/releases/ . CPU lidar example on `gz-sim10`. Headless-rendering docs (recovery only): https://gazebosim.org/api/sim/10/headless_rendering.html |
| ros_gz | **3.0.12**, Apache-2.0. Apt: `ros-lyrical-ros-gz`, `ros-lyrical-ros-gz-sim`, `ros-lyrical-ros-gz-bridge`, `ros-lyrical-ros-gz-interfaces` (and other packages listed in License). Docs: https://docs.ros.org/en/lyrical/p/ros_gz_sim/ , https://docs.ros.org/en/lyrical/p/ros_gz_bridge/ |
| Image | `ros:lyrical-ros-base` digests above. https://hub.docker.com/_/ros . Also tagged `lyrical`, `lyrical-ros-base-resolute`. |
| Runner | `ubuntu-26.04`. Never `ubuntu-latest`. |
| C++ / CMake | C++17, no GNU extensions required, no Eigen. cmake ≥ 3.22 inside the image. |
| GoogleTest | Distro / ament. Version recorded at first green run. |
| gcovr | **8.8**, venv, hashes above. https://pypi.org/project/gcovr/8.8/ |
| Node (host web job) | **26.13.0** Active LTS Lithium (2026-10-28), bundled npm **11.20.0** (https://nodejs.org/en/blog/release/v26.13.0 and `deps/npm/package.json` on tag v26.13.0). Node 20 is EOL (2026-04-30). Committed `web/package-lock.json`. |
| Web | TypeScript **7.0.2**, Vite **8.3.7**, Vitest **5.1.0**, `@playwright/test` **1.65.0**, `@types/node` **26.6.6** (MIT). Chromium only, installed with `playwright install --with-deps chromium`. No separate `playwright` direct dependency unless `@playwright/test` requires it at the same version. Current latest on npm 2026-11-10 for TS/Vite/Vitest/Playwright. |
| Actions (SHA = current floating major tag on 2026-11-10) | checkout v4 `11d5960a326750d5838078e36cf38b85af677262`; setup-node v4 `49933ea5288caeca8642d1e84afbd3f7d6820020`; upload-artifact v4 `ea165f8d65b6e75b540449e92b4886f43607fa02`; download-artifact v4 `d3f86a106a0bac45b974a628896c90dbdf5c8093`; configure-pages v5 `983d7736d9b0ae728b81ab479565c72886d7745b`; deploy-pages v4 `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e`; upload-pages-artifact v3 `56afc609e74202658d3ffba0e8f6dda462b719fa`. Workflows pin the SHAs, not the tags. |

## File layout

```
src/grc_robot/          C++ library + node + primitive SDF
src/grc_bringup/        launch, worlds, bridge yaml, launch_testing, report writer
web/                    Vite + TS dashboard, base '/gazebo-robot-ci/'
web/public/sample-report.json
web/public/badge.svg    placeholder until CI overwrites at deploy
docs/demo.png           checked in once from a local Playwright run
.github/workflows/ci.yml
.github/workflow-pins.md
apt-pins.txt
requirements-ci.txt
LICENSE                 verbatim https://www.apache.org/licenses/LICENSE-2.0.txt
NOTICE
README.md
```

`grc_robot`: `include/grc_robot/follower.hpp`, `safety_stop.hpp`, `types.hpp`; `src/follower.cpp`, `safety_stop.cpp`, `waypoint_follower_node.cpp`; `test/test_follower.cpp`, `test/test_safety.cpp`, `test/test_node.cpp`; `models/grc_diff.sdf`. `grc_bringup`: `launch/sim.launch.py`, `worlds/reach_goal.sdf`, `worlds/stop_obstacle.sdf` (both include the installed robot model), `config/bridge.yaml`, `test/test_s1_reach_goal.py`, `test/test_s2_stop_obstacle.py`, `test/test_s2_mutant.py`, `test/test_s1_brake.py`, `script/write_report.py`. Worlds are self-contained SDF plus the installed model path. No `fuel.gazebosim.org` URIs.

`.gitignore`: `build/`, `install/`, `log/`, `node_modules/`, `dist/`, `__pycache__/`, `*.gcda`, `*.gcno`, local gz logs, local `coverage/`, `.venv/`. Do not commit colcon artifacts. CI writes `artifacts/` as an uploaded artifact; the sample report is the only report committed for local preview.

## Interfaces

Topics (absolute defaults):

- `/cmd_vel` `geometry_msgs/msg/Twist`
- `/odom` `nav_msgs/msg/Odometry`
- `/scan` `sensor_msgs/msg/LaserScan`
- `/waypoints` `nav_msgs/msg/Path` (one Path, one or more poses, `header.frame_id` `odom`)
- `/clock` `rosgraph_msgs/msg/Clock` (one-way gz→ros)
- `/contacts` `ros_gz_interfaces/msg/Contacts` (gz→ros)
- `/grc/status` `std_msgs/msg/String` whose `data` is a one-line JSON object: `{"state":"idle|following|stopped|arrived|scan_timeout","safety_stop":true,"waypoint_index":0,"stop_reason":"none|obstacle|scan_timeout"}`. No custom `.msg` package in v1.

Bridge (https://raw.githubusercontent.com/gazebosim/ros_gz/lyrical/ros_gz_bridge/README.md):

- `/clock` `rosgraph_msgs/msg/Clock` ↔ `gz.msgs.Clock` (GZ_TO_ROS). If Jetty publishes `/world/<world>/clock` rather than `/clock`, remap that gz topic to `/clock` in `bridge.yaml` and record the actual name at first green run.
- `/cmd_vel` `geometry_msgs/msg/Twist` ↔ `gz.msgs.Twist` (ROS_TO_GZ)
- `/odom` `nav_msgs/msg/Odometry` ↔ `gz.msgs.Odometry` (GZ_TO_ROS)
- `/scan` `sensor_msgs/msg/LaserScan` ↔ `gz.msgs.LaserScan` (GZ_TO_ROS)
- `/contacts` `ros_gz_interfaces/msg/Contacts` ↔ `gz.msgs.Contacts` (GZ_TO_ROS)

Parameters: `use_sim_time`, `v_cruise`, `v_max`, `omega_max`, `heading_kp` (1.5), `goal_tol_xy`, `goal_tol_yaw`, `stop_distance` (0.50), `stop_release_margin` (0.10), `forward_half_angle_rad` (0.262), `scan_timeout` (0.5), `safety_stop.enable` (true), `safety_stop.require_scan` (true), `odom_frame` (`odom`), `base_frame` (`base_link`), `laser_frame` (`laser_link`).

C++ library (compiled static lib of the same sources the node uses; gtest links it; no “no-heap” claim - Path handling may allocate):

```text
struct Pose2D { double x, y, yaw; };
struct Twist2D { double v, omega; };
struct FollowerConfig { double v_cruise, v_max, omega_max, goal_tol_xy, goal_tol_yaw, heading_kp; };
struct SafetyConfig { bool enable; bool require_scan; double stop_distance, release_margin,
                      forward_half_angle_rad, scan_timeout_sec; };
enum class DriveState { Idle, Following, Stopped, Arrived, ScanTimeout };
enum class StopReason { None, Obstacle, ScanTimeout };
// Follower::step(pose, path, index, dt) -> Twist2D; advances index; Arrived => (0,0)
// SafetyStop::overlay(cmd, scan, now, last_valid_stamp) -> Twist2D, DriveState, StopReason
```

Node control loop 50 Hz. Odom and scan as published (scan 10 Hz).

Report JSON (`report_version: 1`): `git_sha`, `run_id`, `run_url`, `runner_image` (host `ImageVersion`), `ros_distro` (`lyrical`), `gz_version` (string from `gz sim --version`, or `gz --versions` if that is what the CLI prints - record the exact invocation at first run), `sample` (bool), `honesty` (fixed sentence: simulation only, recorded run, not a live simulator), `scenarios[]` of four rows `{name, pass, expected, observed, sim_duration_s, wall_duration_s, time_to_goal_s|null, time_to_stop_s|null, trip_range_m|null, min_forward_range_m|null, min_clearance_m, contact_count, data_health, reason}` with no NaN or Infinity, `trajectories[]` of `{name, samples:[{t_sim,x,y,yaw}]}` downsampled to ≤ 20 Hz. `expected` / `observed` are short enums (`reach_goal`, `obstacle_stop`, `box_contact`, `miss_goal`, `infra_failure`). `write_report.py` merges per-scenario sidecars with `git rev-parse HEAD` and `GITHUB_RUN_ID`. Downsample by keeping a sample when sim time has advanced by ≥ 0.05 s. A failed suite still writes an honest report and must not be forced to exit 0.

## Scenario gates (falsifiable)

Shared readiness, before the follower is started: `/clock` is advancing, `/odom` is publishing, `/scan` is publishing **valid** scans (all-Inf is valid in S1), and the contact sensor has been proven to exist (at least one Contacts message received, possibly empty). Isolate each test (fresh world, unique ROS domain or sequential runs). Reset telemetry. Wall watchdog on a frozen clock.

**S1 reach_goal.** Empty plane, start (0,0,0), one waypoint (4,0,0) yaw 0. Pass iff contact_count (robot-box; there is no box, so this is zero) is 0, final xy error ≤ 0.20 m and yaw error ≤ 0.30 rad at sim time ≤ 20 s, state becomes `arrived`, and `stop_reason` is never `scan_timeout`. Soft straightness: max |y| ≤ 0.35 m, not a bit-compare. 4 m at 0.40 m/s is 10 s plus accel and settle; 20 s is the conservative sim-time gate.

**S2 stop_obstacle.** Same start and goal, box as locked. Pass iff all of:

1. Readiness as above, then demonstrated forward motion (`odom` x increasing past 0.20 m) and a healthy scan cadence.
2. At least one finite in-range forward measurement **strictly below 0.50 m**, and a `following -> stopped` transition with `stop_reason=obstacle` and a recorded trip stamp and trip range. `scan_timeout`, a sensor outage, a crash, or a readiness failure is an S2 **fail**, not a pass.
3. Within 0.20 s sim after the trip stamp (two 10 Hz scan periods plus control), `abs(cmd.linear.x) ≤ 0.02` and `abs(cmd.angular.z) ≤ 0.05`, then measured odom speed `hypot(vx,vy) ≤ 0.03 m/s` for a 1.0 s dwell. Do not require impossible cross-topic ordering of a scan callback versus an already in-flight command; use stamps.
4. Robot-box `contact_count == 0` for the whole run, and min circle-to-AABB `clearance ≥ 0.15 m` over the whole run (the 0.15 m is a physical margin; ideal clearance at x = 1.26 is 0.39 m, leaving room for control latency). Reaching the goal is **not** required.

**S2 mutant.** Same world and speeds, `safety_stop.enable:=false`. The obstacle overlay is off; the missing-scan fail-safe stays on, and readiness still requires healthy scans. The test **passes CI** only when the contact oracle records a **robot-box** contact (not wheel-ground). Circle-to-AABB penetration is supplemental evidence, not a substitute for a missing contact sensor. A mutant that `scan_timeout`-stops, misses the box, or lacks healthy telemetry **fails** this test. Do not infer contact solely from odometry after impact.

**S1 brake-only.** A launch arg starts the world and publishes zero `cmd_vel` (the follower is not started). The test passes CI only when, with healthy clock and odom through 20 s sim, the pose is not at the goal. A crash or frozen clock is not a pass.

`contact_count` counts robot-obstacle contact pairs (body or wheel link against the box model) observed in `ros_gz_interfaces/msg/Contacts`. Wheel-ground and body-ground contacts are ignored. Silence is not “zero contacts” until the sensor has been proven alive.

## Edge cases

Invalid or all-NaN scans never alone trip the obstacle stop. An all-Inf scan is healthy empty space. A scan whose finite returns all lie outside ±15° does not trip the obstacle stop. Hysteresis: a finite forward range sequence 0.30 → 0.55 stays stopped; 0.30 → 0.60 releases. `safety_stop.enable:=false` never zeroes for range, but still zeroes on `scan_timeout`. Physics is not bit-identical across machines; tests compare sim-time gates, pose tolerances, and contact booleans, never SHA of odom and never wall-clock or frame times.

## Test plan

Unit (no gz process, no `gz`/`ros_gz` DT_NEEDED):

- Pose already inside `goal_tol_xy` and `goal_tol_yaw` of the only waypoint ⇒ `(0,0)`, state Arrived.
- Pose (0,0,0), waypoint (2,0,0), cruise 0.4 ⇒ `v` within 0.02 of 0.40 and `|ω| ≤ 0.05`.
- Same pose, waypoint (0,2,0) (90° left) ⇒ `ω > 0` and `|ω| ≤ 1.20`, `|v| ≤ 0.50`.
- Last waypoint: after xy is reached with a remaining yaw error, `v = 0` and `ω` turns toward the goal yaw, then Arrived.
- Two-waypoint path: index advances after the first xy tolerance, then Arrived on the last.
- Forward finite range 0.30 m ⇒ overlay returns `(0,0)` and `StopReason::Obstacle`.
- Forward finite range 2.0 m, or an all-Inf scan, ⇒ overlay returns the follower command unchanged.
- Hysteresis holds the stop through 0.55 m and releases at 0.60 m.
- NaN, +Inf, and an empty `ranges` array do not update the min; a sibling finite range of 2.0 m still passes the command through.
- No fresh valid scan for > 0.5 s with `require_scan=true` ⇒ `(0,0)`, ScanTimeout.
- `require_scan=false` and no scan ⇒ follower command preserved (gtest only).
- `enable=false` and range 0.30 m ⇒ follower command preserved (and ScanTimeout still applies if `require_scan=true`).
- Thin node test: construct the node (or callback wrapper) without gz and feed a Path plus a synthetic scan.

Sim (`launch_testing` + `launch_testing_ros`, `use_sim_time`): the four gates above, including a dedicated assertion that a synthetic “timeout-stop at x=0 with no trip range” fixture would **not** satisfy the S2 pass predicate (can be a pure predicate unit test on the report helper if cheaper).

Artifacts and web: schema-valid `ci-report.json`; Cobertura XML; badge SVG with `4/4` or `N/4`. Playwright (Chromium) serves built `web/dist` via `vite preview` bound to `127.0.0.1`, fixed port, `baseURL` `http://127.0.0.1:<port>/gazebo-robot-ci/`, no server reuse in CI, `playwright install --with-deps chromium`. Asserts visible “Simulation only” and “Recorded CI output; this page does not run Gazebo.”, **all four** scenario rows and their outcomes, the commit SHA from the JSON, `sample: false` when testing the CI-copied report, a canvas that has drawn trajectory samples (not just axes), no console/page errors, and that `badge.svg` and the report load under `import.meta.env.BASE_URL`. Writes `docs/demo.png`.

## Numbered success criteria

1. `colcon test` of `grc_robot` gtests exits 0 inside `ros:lyrical-ros-base@sha256:3224ee150cb02eb89a5e0811bc267b57ed3a91b9c10191df57810726a7e916d7` (`--platform linux/amd64`) and the test log shows no `gz sim` process.
2. S1 ends with xy error ≤ 0.20 m, yaw error ≤ 0.30 rad, sim time ≤ 20 s, robot-obstacle contact count 0, state `arrived`, and no `scan_timeout`.
3. S2 records a `following -> stopped` transition with `stop_reason=obstacle` and a forward range < 0.50 m, then low command and measured speed as specified, robot-box contact count 0, min circle-to-AABB clearance ≥ 0.15 m, and does not require goal arrival. A `scan_timeout` or missing trip range is an S2 failure.
4. S2 with `safety_stop.enable:=false` produces a robot-box contact, and the dedicated test treats that contact as the expected outcome. The job stays green only when that contact happens with healthy telemetry.
5. Brake-only on S1, with healthy clock and odom through 20 s sim, is not at the goal, and the dedicated test treats that miss as the expected outcome.
6. gcovr 8.8 line coverage of the locked core-library set is ≥ 80% (`--fail-under-line 80`); the node TU is not in that denominator; Cobertura XML and HTML-details are uploaded artifacts.
7. `artifacts/ci-report.json` validates against schema version 1 and includes sha, run id, distro, gz version, exactly four named rows, expectation/observed fields, and ≤ 20 Hz trajectories, with no NaN.
8. The generated badge SVG contains `N/4 expectations passed` and is what Pages serves at `/gazebo-robot-ci/badge.svg`. The README image URL is that path.
9. The dashboard at base `/gazebo-robot-ci/` shows the honesty sentences, the commit SHA, all four rows, and a canvas with trajectory samples, loads JSON via `BASE_URL`, and does not start Gazebo. The deployed report has `sample: false`.
10. Playwright produces `docs/demo.png` locally once and that file is in the repo; CI uploads the screenshot and does not commit it.
11. The single `ci.yml` workflow pins every third-party action to the SHAs in this plan, uses the digest-pinned image via `docker run` on `ubuntu-26.04`, and never uses `ubuntu-latest` or an unpinned `ros:` tag.
12. `LICENSE` is byte-for-byte the Apache-2.0 text from https://www.apache.org/licenses/LICENSE-2.0.txt. `NOTICE` begins `gazebo-robot-ci, Copyright 2026 Arpan Bom` and lists every direct dependency with version and license, including dev dependencies (GoogleTest/ament provider, gcovr 8.8, Vite, Vitest, TypeScript, Playwright Test, `@types/node`, Node/npm, and the ROS, Gazebo, ros_gz, and ros_gz_interfaces apt packages used). Licenses are taken from the installed copyright files, not guessed.
13. Authored source files carry `SPDX-License-Identifier: Apache-2.0`.
14. README states this is not ros2-nav2-slam-sim: no Nav2, no SLAM, no Gazebo Classic, and this repository does run headless `gz sim` in GitHub Actions. It states simulation only, synthetic worlds, not a certified safety stop, not a real robot, and that the dashboard is recorded CI output.
15. `git log` shows author and committer Arpan Bom <applycoding@gmail.com> and no Co-authored-by trailer. README and NOTICE name no assistant or code tool.
16. Tests do not assert wall-clock durations, software-GL or CPU-lidar frame times, or hashes of odom traces.
17. Worlds and meshes ship in-tree. CI performs no Gazebo Fuel download.
18. The `pages` job deploys only on `main` and only after unit, sim, and web jobs of the same SHA succeed. A failed main run keeps the last successful Pages deployment.

## Out of scope

Nav2, slam_toolbox, AMCL, map_server, Gazebo Classic, `gazebo_ros`, ros2_control, xacro, cameras, GPU-hosted runners, a default-path render sensor, Windows or macOS CI, Humble or Jazzy as the default pair, real robot hardware, certified functional safety, a live in-browser Gazebo or a WASM physics port, copying applycoding/ros2-nav2-slam-sim or TurtleBot models, MPPI/TEB/MPC, multi-robot, publishing a derived CI image, and network asset pulls (no Fuel).

## Documentation and honesty

README credits idea sources, not copied code: gazebosim/ros_gz (Apache-2.0, apt dependency, not vendored), gazebosim/gz-sim (Apache-2.0, CPU lidar, DiffDrive, contact system, and headless flags; do not copy tutorial worlds wholesale), ros2/launch and ros2/launch_ros (Apache-2.0, distro `launch_testing*`), ros2/examples (Apache-2.0, shape of a small C++ node only), gazebosim/sdformat and gz-sensors (Apache-2.0, sensor SDF ideas), google/googletest (BSD-3-Clause, via ament, not vendored). ros-controls/gz_ros2_control is Apache-2.0 and idea-only; v1 uses stock DiffDrive. Do not copy TurtleBot, Nav2, or ros2-nav2-slam-sim worlds or prose. Do not vendor GPL or LGPL projects. README, Pages, and the report repeat: simulation only; synthetic worlds; not Nav2; not SLAM; not Gazebo Classic; not a real robot; not a certified safety function; the dashboard is recorded CI output and does not run Gazebo.

## License

Outbound **Apache-2.0**, not MIT. LICENSE is the verbatim official text from https://www.apache.org/licenses/LICENSE-2.0.txt (download that URL at repo creation; do not retype it). NOTICE lists name, version, and license for direct and dev dependencies actually installed or declared, taken from their own files. Minimum inventory, versions filled at first green run where this plan says “record”:

- ROS 2 Lyrical packages actually installed, including `ros-lyrical-ros-gz` 3.0.12, `ros-lyrical-ros-gz-sim`, `ros-lyrical-ros-gz-bridge`, `ros-lyrical-ros-gz-interfaces`, `ros-lyrical-rclcpp`, `ros-lyrical-nav-msgs`, `ros-lyrical-sensor-msgs`, `ros-lyrical-geometry-msgs`, `ros-lyrical-std-msgs`, `ros-lyrical-rosgraph-msgs`, `ros-lyrical-tf2-ros`, `ros-lyrical-launch-testing`, `ros-lyrical-launch-testing-ament-cmake`, `ros-lyrical-launch-testing-ros`, `ros-lyrical-ament-cmake-gtest`, and any `ros-lyrical-gz-*-vendor` packages pulled in. Confirm each name and license with `apt-cache show` / the installed copyright file. Do not blanket-label every ROS package Apache-2.0 without checking.
- Gazebo Jetty libraries pulled by those metapackages, one NOTICE line per relevant apt package, with the Debian version string.
- Mesa / GL packages only if the recovery path is installed; do not label GLVND (`libegl1`, `libgl1`) as “Mesa MIT.” Record each package’s own license.
- GoogleTest via the distro/ament provider (BSD-3-Clause), version from the installed package.
- gcovr 8.8 (BSD-3-Clause). gcc/gcov is the image toolchain (named as a system compiler, not vendored). A system GPL compiler does not relicense authored source.
- Node 26.13.0 (MIT), npm 11.20.0, TypeScript 7.0.2 (Apache-2.0), Vite 8.3.7 (MIT), Vitest 5.1.0 (MIT), `@playwright/test` 1.65.0 (Apache-2.0), `@types/node` 26.6.6 (MIT). Include the Playwright Chromium notice if the browser is redistributed; a CI-only install that is not shipped in the Pages bundle is listed as a test tool, not as a shipped dependency.

Do not copy MIT-licensed text from applycoding/ros2-nav2-slam-sim.

## Build and CI

One workflow, `.github/workflows/ci.yml`, all jobs `runs-on: ubuntu-26.04`:

- `unit` - `docker run` as locked. Inside: `apt-get update` and install the pinned packages; create a venv; `pip install` hashed gcovr 8.8. `colcon build --packages-select grc_robot --cmake-args -DCMAKE_BUILD_TYPE=Debug` with compile and link `--coverage`. `colcon test --packages-select grc_robot` then `colcon test-result --verbose`. gcovr as locked. Upload coverage. Do not start gz. `timeout-minutes: 15`.
- `sim` - parallel with `unit`. Same image and apt pins, Release build of both packages (coverage flags optional here). `launch_test` the four tests. Then `write_report.py` and the badge writer. Upload `artifacts/` and logs (`if: always()`). `timeout-minutes: 40`.
- `web` - `needs: [sim]`. `actions/setup-node` SHA with `node-version: 26.13.0` and `cache: npm`, `cache-dependency-path: web/package-lock.json`. `npm ci` in `web/`. Vitest. `vite build`. Download the sim artifact. Copy `ci-report.json` to `web/dist/ci-report.json` (and the same path the app fetches via `BASE_URL`) and regenerate `web/dist/badge.svg` from it **before** Playwright. Playwright as locked. Upload the screenshot and the **tested** `web/dist`. `timeout-minutes: 15`.
- `pages` - `needs: [unit, sim, web]`, `if: github.ref == 'refs/heads/main' && github.event_name == 'push'`, environment `github-pages`, permissions `pages: write` and `id-token: write` on that job only. Deploy the tested `web/dist` already containing the report and badge. Concurrency group `pages` without cancel-in-progress. PR concurrency may cancel in progress. Fork PRs receive no secrets. No `pull_request_target`. A failed main run must not replace a previously successful Pages deployment with a sample or failed report.

Local reproduction matches CI: the same `docker run` line, the same apt pins, `DISPLAY=` empty, `--shm-size=1g`. README gives that command and states the dashboard preview is `vite preview` against `sample-report.json`.

## Risks

CPU lidar still needs DART+Bullet; a wrong collision detector yields silent empty scans and must fail readiness, not S2-pass. First gz start and apt install of ros-gz can be slow; the 40-minute ceiling is a budget, not a measurement. Apt drift inside a digest-pinned base image is real and is accepted only with pins and an uploaded resolution log. `ubuntu-latest` migration can silently change the host; the workflow must spell `ubuntu-26.04`. Physics non-determinism forbids trace hashes. Laser self-hit is avoided by the locked z placement; changing the body height without moving the laser will break S2. Contact silence without a proven sensor would hide collisions; readiness forbids that. The Jazzy + Harmonic fallback stays unused unless Lyrical + Jetty is shown broken with logs.
