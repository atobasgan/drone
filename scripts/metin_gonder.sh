#!/usr/bin/env bash
# Faz 2: /voice/text'e Turkce cumle gonderir (parser_node dinler).
#   ./scripts/metin_gonder.sh "önce 20 metre yüksel sonra kuzeye 50 metre git"
set -euo pipefail
[ $# -ge 1 ] || { sed -n '2,3p' "$0"; exit 1; }
metin="${*//\'/\'\'}"
ros2 topic pub --once /voice/text std_msgs/msg/String "{data: '$metin'}"
