# gazebo-robot-ci

Portfolio demo by **Arpan Bom** (`applycoding@gmail.com`). A small C++ ROS 2 waypoint follower with a teaching safety-stop overlay, tested with **gtest** (no Gazebo) and headless **Gazebo Jetty** `launch_testing` scenarios on GitHub Actions. A static dashboard on GitHub Pages shows **recorded CI output** only - it does not run Gazebo.

**Simulation only.** Synthetic worlds; not Nav2; not SLAM; not Gazebo Classic; not a real robot; not a certified safety function. Unlike [applycoding/ros2-nav2-slam-sim](https://github.com/applycoding/ros2-nav2-slam-sim) (Humble + Gazebo Classic, no sim in CI), **this repository does run** `gz sim` headlessly in Actions.

Licensed under the [Apache License, Version 2.0](LICENSE). SPDX headers in authored sources.

## Stack

- ROS 2 **Lyrical** + Gazebo **Jetty** via `ros-lyrical-ros-gz` **3.0.10** (recorded in `apt-pins.txt`; PLAN targeted 3.0.12)
- GPU lidar (`type="gpu_lidar"` with `gz-sim-sensors-system` and Mesa software rendering; `gz-sim-cpu-lidar-system` is not in the Lyrical vendor tree), DART+Bullet, contact oracles
- Digest-pinned CI image: `ros:lyrical-ros-base@sha256:3224ee150cb02eb89a5e0811bc267b57ed3a91b9c10191df57810726a7e916d7`
- Hosted runner: `ubuntu-26.04` (never `ubuntu-latest`)

## Dashboard

After a green `main` run, Pages serves the tested `web/dist` at base `/gazebo-robot-ci/`.

![CI badge](/gazebo-robot-ci/badge.svg)

Local preview: `cd web && npm ci && npm run dev` (loads `sample-report.json`). Example screenshot: [docs/demo.png](docs/demo.png) (recorded from a local Playwright run).

## Local reproduction (container)

```bash
docker run --rm --init --platform linux/amd64 \
  -v "$PWD:/ws" -w /ws --shm-size=1g \
  -e DISPLAY= -e LIBGL_ALWAYS_SOFTWARE=1 \
  ros:lyrical-ros-base@sha256:3224ee150cb02eb89a5e0811bc267b57ed3a91b9c10191df57810726a7e916d7 \
  bash
# inside: source /opt/ros/lyrical/setup.bash, install ros-gz per apt-pins.txt, colcon build, colcon test
```

## References

See [REFERENCES.md](REFERENCES.md) for permissively licensed projects used as **references only** (not copied). `ros_gz` and Gazebo Jetty are apt dependencies.

## Author

Arpan Bom - `applycoding@gmail.com`
