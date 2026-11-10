#!/usr/bin/env bash
# Bir GGUF modelini llama-server'da acar, finetune.eval.olc ile olcer, sunucuyu kapatir.
#   finetune/eval/model_olc.sh <model.gguf> <etiket> <ft:evet|hayir> <quant> [--kisa-prompt] [--tam-hat]
# Ornek (Gorev 4.4 baseline):
#   finetune/eval/model_olc.sh models/qwen3-0.6b-q4_k_m.gguf "qwen3-0.6b (CPU 4c)" hayir Q4_K_M
set -euo pipefail
cd "$(dirname "$0")/../.."
MODEL_YOLU="$1"; ETIKET="$2"; FT="$3"; QUANT="$4"; shift 4
PORT="${PORT:-8091}"
# Onceki olcumun sunucusu hala kapaniyorsa port dolu olur ve yenisi acilmaz: bosalmasini bekle.
for _ in $(seq 30); do curl -s "http://127.0.0.1:$PORT/health" >/dev/null || break; sleep 1; done
MODEL="$MODEL_YOLU" PORT="$PORT" CTX="${CTX:-2048}" ./scripts/llama_server.sh >/tmp/llama_olc.log 2>&1 &
SUNUCU=$!
trap 'kill $SUNUCU 2>/dev/null; wait $SUNUCU 2>/dev/null || true' EXIT
for _ in $(seq 120); do
  curl -sf "http://127.0.0.1:$PORT/health" >/dev/null && break
  kill -0 $SUNUCU 2>/dev/null || { echo "llama-server açılamadı (/tmp/llama_olc.log)"; exit 1; }
  sleep 1
done
python3 -m finetune.eval.olc --url "http://127.0.0.1:$PORT" --etiket "$ETIKET" --ft "$FT" --quant "$QUANT" "$@"
