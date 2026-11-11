#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -eo pipefail

SCENARIO="${1:?scenario name required}"
WORLD="${2:?world sdf filename required}"
START_FOLLOWER="${3:-true}"
SAFETY_ENABLE="${4:-true}"
ARTIFACTS="${GRC_ARTIFACTS_DIR:-/ws/artifacts}"
if [[ -n "${5:-}" ]]; then
  export ROS_DOMAIN_ID="$5"
else
  export ROS_DOMAIN_ID="$(python3 -c "print(10 + hash('${SCENARIO}') % 80)")"
fi
export GRC_ARTIFACTS_DIR="$ARTIFACTS"
mkdir -p "$ARTIFACTS/scenarios"
pkill -x gz-sim-server 2>/dev/null || true
pkill -f "ruby /usr/bin/gz" 2>/dev/null || true
sleep 1

bash -lc "
  set -eo pipefail
  source /opt/ros/lyrical/setup.bash
  source /ws/install/setup.bash
  export GZ_SIM_RESOURCE_PATH=/ws/install/grc_robot/share/grc_robot/models
  export GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/ros/lyrical/lib:/opt/ros/lyrical/opt/gz_sim_vendor/lib:/opt/ros/lyrical/opt/gz_plugins_vendor/lib:/opt/ros/lyrical/opt/gz_sensors_vendor/lib
  export GZ_PLUGIN_PATH=\$GZ_SIM_SYSTEM_PLUGIN_PATH
  export LIBGL_ALWAYS_SOFTWARE=1
  export LIBGL_DRI3_DISABLE=1
  export GZ_PARTITION=grc_${SCENARIO}
  GOAL_BYPASS=false
  LATCH_RELEASE=true
  if [[ \"${SCENARIO}\" == s1 || \"${SCENARIO}\" == s1_brake_expects_miss ]]; then
    GOAL_BYPASS=true
  fi
  if [[ \"${SCENARIO}\" == s2 ]]; then
    LATCH_RELEASE=false
  fi
  GOAL_X=4.0
  GOAL_Y=0.0
  if [[ \"${SCENARIO}\" == s2_mutant_expects_contact ]]; then
    GOAL_X=2.2
  fi
  ros2 launch grc_bringup sim.launch.py \\
    world:=/ws/install/grc_bringup/share/grc_bringup/worlds/${WORLD} \\
    start_follower:=${START_FOLLOWER} \\
    safety_stop_enable:=${SAFETY_ENABLE} \\
    goal_safety_bypass:=\${GOAL_BYPASS} \\
    latch_release_enable:=\${LATCH_RELEASE} \\
    goal_x:=\${GOAL_X} goal_y:=\${GOAL_Y} &
  LAUNCH_PID=\$!
  sleep 3
  set +e
  ros2 run grc_bringup run_scenario_test.py --scenario ${SCENARIO} --artifacts-dir ${ARTIFACTS}
  if [[ \"${SCENARIO}\" == s2 || \"${SCENARIO}\" == s2_mutant_expects_contact ]]; then
    /ws/install/grc_bringup/lib/grc_bringup/collect_gz_contact_debug.sh \"${ARTIFACTS}\" \"${SCENARIO}\" || true
    timeout 2 gz topic -e -t /grc/robot_lc_contacts -n 1 > \"${ARTIFACTS}/gz_contact_echo_${SCENARIO}.txt\" 2>&1 || true
  fi
  SIDECAR=${ARTIFACTS}/scenarios/${SCENARIO}.json
  if [[ ! -f \$SIDECAR ]]; then
    echo missing sidecar \$SIDECAR
    exit 2
  fi
  EXIT=\$(python3 -c \"import json,sys; d=json.load(open('${ARTIFACTS}/scenarios/${SCENARIO}.json')); print(0 if d.get('pass') else 1)\")
  kill \$LAUNCH_PID 2>/dev/null || true
  pkill -x gz-sim-server 2>/dev/null || true
  sleep 1
  exit \$EXIT
"
