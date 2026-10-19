#!/usr/bin/env bash
# "Her seyi baslat" (Gorev 0.7): tmux icinde her surec ayri pencerede.
#   ./scripts/hepsini_baslat.sh          # sim + agent + llm + ros node'lari
#   ./scripts/hepsini_baslat.sh faz1     # sim + agent + sadece executor
#   HEADLESS=1 ./scripts/hepsini_baslat.sh   # Gazebo penceresiz
# Kapatmak: tmux kill-session -t drone
set -euo pipefail
source "$(dirname "$0")/ortam.sh"
MOD="${1:-hepsi}"
OTURUM=drone

command -v tmux >/dev/null || { echo "tmux gerekli: sudo apt install tmux"; exit 1; }
tmux has-session -t $OTURUM 2>/dev/null && { echo "zaten calisiyor: tmux attach -t $OTURUM"; exit 0; }

ROS_SRC="source /opt/ros/$ROS_DISTRO/setup.bash && source $LLM_DRONE_DIR/ros2_ws/install/setup.bash"

tmux new-session -d -s $OTURUM -n px4 \
  "cd $PX4_DIR && PX4_HOME_LAT=$PX4_HOME_LAT PX4_HOME_LON=$PX4_HOME_LON PX4_HOME_ALT=$PX4_HOME_ALT HEADLESS=${HEADLESS:-} make px4_sitl gz_x500; bash"
tmux new-window -t $OTURUM -n agent "MicroXRCEAgent udp4 -p 8888; bash"

if [ "$MOD" = "faz1" ]; then
  tmux new-window -t $OTURUM -n ros "$ROS_SRC && sleep 8 && ros2 launch drone_bringup executor.launch.py; bash"
else
  tmux new-window -t $OTURUM -n llm "$LLM_DRONE_DIR/scripts/llama_server.sh; bash"
  tmux new-window -t $OTURUM -n ros "$ROS_SRC && sleep 8 && ros2 launch drone_bringup all.launch.py; bash"
fi
tmux new-window -t $OTURUM -n terminal "$ROS_SRC && bash"
tmux attach -t $OTURUM
