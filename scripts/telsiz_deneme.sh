#!/usr/bin/env bash
# Telsiz uygulamasini ROS/PX4 OLMADAN dene: gercek command_parser + guvenlik
# katmani, sanal drone. Telefonda terminaldeki QR kodu okut.
#   ./scripts/telsiz_deneme.sh                                  # sadece hizli yol
#   ./scripts/telsiz_deneme.sh --llm http://127.0.0.1:8080      # + LLM
#   ./scripts/telsiz_deneme.sh --stt faster_whisper             # yer STT modu
# Gerekli: pip install websockets requests (yer STT icin: faster-whisper)
set -euo pipefail
kok="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$kok/ros2_ws/src/mobile_bridge:$kok/ros2_ws/src/command_parser:$kok/ros2_ws/src/mission_executor${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m mobile_bridge.deneme_sunucusu "$@"
