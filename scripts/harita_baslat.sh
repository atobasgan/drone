#!/usr/bin/env bash
# Faz 5: hepsini_baslat.sh'in harita'li hali (tmux). all.launch.py yerine harita.launch.py.
#   ./scripts/harita_baslat.sh                 # sim + agent + llm + harita.launch.py
#   FT=1 ./scripts/harita_baslat.sh            # Faz 5 fine-tune'lu model (FT5_MODEL) + kisa prompt
#   HEADLESS=1 ./scripts/harita_baslat.sh      # Gazebo penceresiz
#   GOOGLE_MAPS_API_KEY=... HARITA_YAML=.../harita_google.yaml ./scripts/harita_baslat.sh
# Kapatmak: tmux kill-session -t drone
set -euo pipefail
source "$(dirname "$0")/ortam.sh"
OTURUM=drone
FT5_MODEL="${FT5_MODEL:-$LLM_DRONE_DIR/finetune/models/drone-0.6b-faz5/drone-0.6b-faz5-q8_0.gguf}"

command -v tmux >/dev/null || { echo "tmux gerekli: sudo apt install tmux"; exit 1; }
tmux has-session -t $OTURUM 2>/dev/null && { echo "zaten calisiyor: tmux attach -t $OTURUM"; exit 0; }

ROS_SRC="source /opt/ros/$ROS_DISTRO/setup.bash && source $LLM_DRONE_DIR/ros2_ws/install/setup.bash"
LAUNCH_ARG=""
[ -n "${HARITA_YAML:-}" ] && LAUNCH_ARG="harita:=$HARITA_YAML"
if [ -n "${FT:-}" ]; then
  LLM_KOMUT="MODEL=$FT5_MODEL CTX=1024 $LLM_DRONE_DIR/scripts/llama_server.sh"
  LAUNCH_ARG="$LAUNCH_ARG ft:=true"
else
  LLM_KOMUT="$LLM_DRONE_DIR/scripts/llama_server.sh"
fi

tmux new-session -d -s $OTURUM -n px4 \
  "cd $PX4_DIR && PX4_HOME_LAT=$PX4_HOME_LAT PX4_HOME_LON=$PX4_HOME_LON PX4_HOME_ALT=$PX4_HOME_ALT HEADLESS=${HEADLESS:-} make px4_sitl gz_x500; bash"
tmux new-window -t $OTURUM -n agent "MicroXRCEAgent udp4 -p 8888; bash"
tmux new-window -t $OTURUM -n llm "$LLM_KOMUT; bash"
tmux new-window -t $OTURUM -n ros \
  "$ROS_SRC && sleep 8 && GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY:-} ros2 launch drone_bringup harita.launch.py $LAUNCH_ARG; bash"
tmux new-window -t $OTURUM -n terminal "$ROS_SRC && bash"
tmux attach -t $OTURUM
