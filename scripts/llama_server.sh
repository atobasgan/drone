#!/usr/bin/env bash
# Gorev 2.3: llama-server'i baslat. Model bir kez yuklenir, hep bellekte kalir.
#   ./scripts/llama_server.sh                       # varsayilan: qwen3-0.6b
#   MODEL=qwen3-1.7b-q4_k_m.gguf ./scripts/llama_server.sh
#   NGL=0 ./scripts/llama_server.sh                 # GPU'yu kullanma
#
# -c 2048: Faz 2'nin few-shot sistem prompt'u ~800 token. Faz 4'te kisa prompt'lu
#          fine-tune'lu modelde 1024'e indirilebilir.
# -np 1  : tek slot -> sistem prompt'u KV-cache'te tekrar kullanilir (cache_prompt).
# --jinja: modelin kendi sohbet sablonu (enable_thinking=false icin gerekli).
set -euo pipefail
source "$(dirname "$0")/ortam.sh"
MODEL="${MODEL:-qwen3-0.6b-q4_k_m.gguf}"
[ -f "$MODEL" ] || MODEL="$MODEL_DIR/$MODEL"
if [ -z "${NGL:-}" ]; then
  if command -v nvidia-smi >/dev/null 2>&1; then NGL=99; else NGL=0; fi
fi
# CPU'da STT ile cekirdek kavgasi olmasin diye thread sayisini elle ver (MIMARI 9.2/17)
THREADS="${THREADS:-$(( $(nproc) / 2 > 0 ? $(nproc) / 2 : 1 ))}"

exec "$LLAMA_CPP_DIR/build/bin/llama-server" \
  -m "$MODEL" --host 127.0.0.1 --port "${PORT:-8080}" \
  -c "${CTX:-2048}" -ngl "$NGL" -t "$THREADS" -np 1 --jinja
