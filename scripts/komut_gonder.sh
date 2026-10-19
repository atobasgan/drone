#!/usr/bin/env bash
# Faz 1: terminalden /drone/command'a komut gonderir (LLM yok).
#   ./scripts/komut_gonder.sh "{komut: 'kalk', metre: 10.0}"
#   ./scripts/komut_gonder.sh "{komut: 'yuksel', metre: 50.0}"
#   ./scripts/komut_gonder.sh "{komut: 'don', yon: 'sag', derece: 90.0}" "{komut: 'git_yon', yon: 'ileri', metre: 20.0}"
#   EKLE=true ./scripts/komut_gonder.sh "{komut: 'eve_don'}"     # kuyrugun sonuna ekle
set -euo pipefail
[ $# -ge 1 ] || { sed -n '2,7p' "$0"; exit 1; }
adimlar=$(IFS=,; echo "$*")
ros2 topic pub --once /drone/command drone_interfaces/msg/CommandList \
  "{adimlar: [$adimlar], kuyruga_ekle: ${EKLE:-false}, kaynak: 'terminal'}"
