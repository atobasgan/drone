#!/usr/bin/env bash
# Birlestirilmis modeli GGUF'a cevirir ve quantize eder (Gorev 4.5 son adim, 4.6 Q4/Q8 kiyasi).
#   finetune/train/disa_aktar.sh drone-0.6b
# Cikti: finetune/models/<ad>/<ad>-f16.gguf, <ad>-q4_k_m.gguf, <ad>-q8_0.gguf
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/ortam.sh
AD="${1:-drone-0.6b}"
KLASOR="finetune/models/$AD"
[ -d "$KLASOR/hf" ] || python3 -m finetune.train.birlestir --ad "$AD"
PYTHONPATH="$LLAMA_CPP_DIR/gguf-py" python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" "$KLASOR/hf" \
  --outtype f16 --outfile "$KLASOR/$AD-f16.gguf"
for Q in Q4_K_M Q8_0; do
  "$LLAMA_CPP_DIR/build/bin/llama-quantize" "$KLASOR/$AD-f16.gguf" \
    "$KLASOR/$AD-$(echo "$Q" | tr 'A-Z' 'a-z').gguf" "$Q"
done
ls -lh "$KLASOR"/*.gguf
