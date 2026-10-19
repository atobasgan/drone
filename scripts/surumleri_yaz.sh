#!/usr/bin/env bash
# Calisan surumleri NOTLAR.md'ye eklenecek bicimde yazar (Gorev 0.7).
source "$(dirname "$0")/ortam.sh"
git_bilgi() { [ -d "$1/.git" ] && git -C "$1" describe --tags --always 2>/dev/null || echo "yok"; }
echo "## Surumler ($(date +%F))"
echo "- Ubuntu        : $(. /etc/os-release && echo "$PRETTY_NAME")"
echo "- ROS 2         : $ROS_DISTRO"
echo "- Gazebo        : $(gz sim --version 2>/dev/null | head -1 || echo yok)"
echo "- PX4           : $(git_bilgi "$PX4_DIR")"
echo "- px4_msgs      : $(git_bilgi "$LLM_DRONE_DIR/ros2_ws/src/px4_msgs") ($(git -C "$LLM_DRONE_DIR/ros2_ws/src/px4_msgs" rev-parse --abbrev-ref HEAD 2>/dev/null))"
echo "- XRCE Agent    : $(git_bilgi "$XRCE_AGENT_DIR")"
echo "- llama.cpp     : $(git_bilgi "$LLAMA_CPP_DIR")"
echo "- GPU           : $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo yok)"
echo "- CPU / RAM     : $(nproc) cekirdek / $(free -h | awk '/Mem:/{print $2}')"
