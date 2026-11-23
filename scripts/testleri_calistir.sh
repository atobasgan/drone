#!/usr/bin/env bash
# ROS gerektirmeyen birim testleri (safety, geo, normalize, hizli yol, sema, LLM istemcisi,
# VAD, gecikme olcumu, Faz 4 veri uretimi).
set -euo pipefail
kok="$(cd "$(dirname "$0")/.." && pwd)"
for paket in mission_executor command_parser voice_input latency_monitor; do
  echo "=== $paket ==="
  (cd "$kok/ros2_ws/src/$paket" && python3 -m pytest -q "$@")
done
echo "=== finetune (Faz 4 veri uretimi ve degerlendirme) ==="
(cd "$kok" && python3 -m pytest -q finetune/test "$@")
echo "=== sahte simulasyon (executor + parser, ROS'suz) ==="
python3 "$kok/araclar/sahte_sim/sim.py" | tail -1
echo "=== map_tools (Faz 5 harita komutlari) ==="
(cd "$kok/ros2_ws/src/map_tools" && python3 -m pytest -q "$@")
echo "=== sahte simulasyon (Faz 5: parser + harita_node + executor) ==="
python3 "$kok/araclar/sahte_sim/sim_harita.py" | tail -1
