#!/usr/bin/env bash
# ros2_ws'i derler. Ilk derlemede px4_msgs uzun surer.
#   ./scripts/derle.sh                    # hepsi
#   ./scripts/derle.sh mission_executor   # sadece bir paket (ve bagimliliklari)
set -eo pipefail
source "$(dirname "$0")/ortam.sh"
source "/opt/ros/$ROS_DISTRO/setup.bash"
cd "$LLM_DRONE_DIR/ros2_ws"
if [ $# -gt 0 ]; then
  colcon build --symlink-install --packages-up-to "$@"
else
  colcon build --symlink-install
fi
echo "Simdi: source $LLM_DRONE_DIR/ros2_ws/install/setup.bash"
