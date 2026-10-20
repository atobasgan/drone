#!/usr/bin/env bash
# Telefon uygulamasinin GERCEK Dart istemcisi ile Python koprusunun birlikte
# calistigini dogrular (protokol, ikili ses cerceveleri, komut/geri bildirim).
# Gerekli: Flutter SDK, pip install websockets requests
set -euo pipefail
kok="$(cd "$(dirname "$0")/.." && pwd)"
port=$((20000 + RANDOM % 20000))
"$kok/scripts/telsiz_deneme.sh" --host 127.0.0.1 --port "$port" --token UYUM \
  --sahte-stt "20 metre yüksel" --hiz 20 > /tmp/telsiz_uyum_sunucu.log 2>&1 &
sunucu=$!
trap 'kill $sunucu 2>/dev/null || true' EXIT
for _ in $(seq 50); do grep -q "Deneme sunucusu" /tmp/telsiz_uyum_sunucu.log && break; sleep 0.1; done
cd "$kok/mobil"
TELSIZ_UYUM_URL="ws://127.0.0.1:$port/telsiz?token=UYUM" flutter test test/uyum_test.dart "$@"
echo "--- sunucu günlüğü ---"; grep -v '^$' /tmp/telsiz_uyum_sunucu.log | grep '^  ' || true
