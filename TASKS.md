# Build tasks - gazebo-robot-ci

Execute in order. Follow PLAN.md. Deviate only if a pin or test proves a step broken, and record why. License is **Apache-2.0**, not MIT. Commit author and committer are always **Arpan Bom <applycoding@gmail.com>**. No `Co-authored-by` trailer. No tool credit in the repository.

Each task has acceptance checks. A task is done only when those checks pass.

## 1. Repository skeleton and license

- Create the tree in PLAN.md (empty dirs may hold `.gitkeep`).
- Fetch `https://www.apache.org/licenses/LICENSE-2.0.txt` into `LICENSE` and confirm byte equality (including the appendix).
- Write `NOTICE` starting with `gazebo-robot-ci, Copyright 2026 Arpan Bom`, then dependency notices (filled as pins land) per PLAN.md.
- README stub: portfolio demo, simulation only, Apache-2.0, author Arpan Bom, teaching waypoint follower, not Nav2, not a certified safety stop, not ros2-nav2-slam-sim, and this repo does run headless `gz sim` in Actions.
- Package.xml / CMake skeletons for `grc_robot` and `grc_bringup`. SPDX on authored files.
- `.gitignore` as in PLAN.md.

**Accept:** `cmp LICENSE` against a fresh curl of the official text exits 0. NOTICE and README name Apache-2.0 and Arpan Bom.

## 2. Pin the container, apt, and gcovr

- Commit `.github/workflow-pins.md` with the image index and amd64 digests, the Action SHAs, Node 26.13.0, and npm 11.20.0 from PLAN.md.
- Write `apt-pins.txt` with at least `ros-lyrical-ros-gz=3.0.12-1resolute` (confirm the exact revision inside the digest-pinned image and correct it if the revision suffix differs).
- Write hashed `requirements-ci.txt` for gcovr 8.8 (wheel sha256 in PLAN.md).
- A first `docker run --platform linux/amd64` of the digest-pinned image must succeed and print the image's cmake and python3 versions into the pins file.

**Accept:** Criterion 11's digest and SHA parts can be written into `ci.yml` from this file. Digest pull does not 404.

## 3. Follower and safety-stop library

- Implement `Follower` and `SafetyStop` exactly as in PLAN.md (`heading_kp = 1.5`, last-waypoint yaw-only, all-Inf is healthy, scan_timeout distinct from obstacle stop).
- No gz or ros_gz link in the library.

**Accept:** The unit cases listed in PLAN.md's Test plan (already-at-goal, 2 m cruise, 90° turn, last-waypoint yaw, two waypoints, 0.30 m stop, 2.0 m and all-Inf pass-through, hysteresis, NaN/empty, scan_timeout, require_scan=false, enable=false).

## 4. rclcpp node and thin node test

- Implement `grc_waypoint_follower` with the locked topics, parameters, and `/grc/status` JSON, `use_sim_time` supported, 50 Hz control loop.
- Thin gtest constructs the node or callback wrapper without starting gz.

**Accept:** Node test passes in the container with no `gz sim` process (criterion 1, node part).

## 5. In-tree SDF robot and worlds

- One installed `models/grc_diff.sdf`: primitives, DiffDrive fields, CPU lidar, contact sensor on the body, laser at (0.12, 0, 0.27), geometry as locked. No xacro, no Fuel.
- Worlds `reach_goal.sdf` and `stop_obstacle.sdf`: DART + Bullet, 1 ms step, Physics + CpuLidar + Contact systems, no GPU sensors system, no cameras. S2 box 0.40 m at (2.0, 0.0, 0.20).
- `bridge.yaml` with the locked type mappings, including `ros_gz_interfaces/msg/Contacts` and `/clock`. Record the actual gz clock topic if it is not `/clock`.

**Accept:** `gz sdf --check` (or the Jetty equivalent) on the model and both worlds exits 0. A local or container `gz sim -s -r` of each world produces `/scan` (or the gz lidar topic) and contact messages without a render engine.

## 6. launch_testing gates

- Implement the four tests with the readiness, watchdog, and pass predicates in PLAN.md.
- S2 requires an obstacle trip (`stop_reason=obstacle` and a range < 0.50). A timeout-stop must not pass S2.
- Mutant requires a robot-box contact with healthy telemetry. Brake-only requires a healthy 20 s miss.
- `contact_count` ignores ground contacts. Circle-to-AABB clearance is the S2 margin gate.
- Sidecar JSON per scenario for the report writer.
- Predicate unit test (or equivalent) that a timeout-stop fixture fails the S2 pass predicate.

**Accept:** Criteria 2-5. Do not move the box or slow the robot to pass.

## 7. Report, badge, coverage, unit CI job

- `write_report.py` emits schema v1 with exactly four named rows, expectation/observed fields, no NaN.
- Badge text `N/4 expectations passed`.
- gcovr 8.8 in a venv, filters and `--fail-under-line 80` as locked.
- `unit` job in `ci.yml` as in PLAN.md.

**Accept:** Criteria 6-8 (report and coverage parts). Core-library coverage ≥ 80%.

## 8. Pages dashboard and Playwright

- Vite app, `base: '/gazebo-robot-ci/'`, Canvas 2D trajectories, four-row table, honesty labels, fetches via `import.meta.env.BASE_URL`.
- Committed `sample-report.json` with `sample: true`. Deployed CI report has `sample: false` and is not replaced by the sample on `main`.
- Playwright as locked (127.0.0.1, fixed port, all four rows, trajectory samples not just axes, Chromium with deps).
- Check in `docs/demo.png` locally once. CI uploads the screenshot and does not commit it.

**Accept:** Criteria 9-10.

## 9. Single workflow, pages job, README honesty

- One `ci.yml`: `unit` and `sim` independent, `web` needs `sim` and copies report/badge before Playwright, `pages` needs all three and deploys only a main push of that SHA. SHA-pinned actions, digest-pinned `docker run` on `ubuntu-26.04`. No `ubuntu-latest`, no `pull_request_target`, no second workflow.
- Finish README and NOTICE as in criteria 12-15, 17-18, including differentiation from ros2-nav2-slam-sim and a full dev-dependency inventory.

**Accept:** Criteria 11-18. Commit author is Arpan Bom `<applycoding@gmail.com>`.
