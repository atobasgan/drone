#!/usr/bin/env bash
# ROS gerektirmeyen birim testleri (safety, geo, normalize, hizli yol, sema, LLM istemcisi).
set -euo pipefail
kok="$(cd "$(dirname "$0")/.." && pwd)"
for paket in mission_executor command_parser; do
  echo "=== $paket ==="
  (cd "$kok/ros2_ws/src/$paket" && python3 -m pytest -q "$@")
done
echo "=== sahte simulasyon (executor + parser, ROS'suz) ==="
python3 "$kok/araclar/sahte_sim/sim.py" | tail -1
