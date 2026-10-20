#!/usr/bin/env bash
# ROS gerektirmeyen tum testler:
#   - birim testleri (safety, geo, normalize, hizli yol, sema, LLM istemcisi, telsiz koprusu)
#   - sahte simulasyonlar (executor + parser; telsiz koprusu + executor + parser)
#   - Flutter testleri ve telefon <-> kopru uyum testi (Flutter SDK varsa)
set -euo pipefail
kok="$(cd "$(dirname "$0")/.." && pwd)"
for paket in mission_executor command_parser mobile_bridge; do
  echo "=== $paket ==="
  (cd "$kok/ros2_ws/src/$paket" && python3 -m pytest -q "$@")
done
echo "=== sahte simulasyon (executor + parser, ROS'suz) ==="
python3 "$kok/araclar/sahte_sim/sim.py" | tail -1
echo "=== telsiz simulasyonu (mobile_bridge + parser + executor, ROS'suz) ==="
python3 "$kok/araclar/sahte_sim/telsiz_sim.py" 2>/dev/null | tail -1
if command -v flutter >/dev/null; then
  echo "=== Flutter (mobil) ==="
  (cd "$kok/mobil" && flutter analyze --no-pub && flutter test --no-pub)
  echo "=== telefon <-> köprü uyum testi ==="
  "$kok/scripts/telsiz_uyum_testi.sh" --no-pub | grep -E "All tests|failed"
else
  echo "(flutter yok: mobil testleri atlandı)"
fi
