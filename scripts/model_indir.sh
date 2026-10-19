#!/usr/bin/env bash
# Gorev 2.3: Faz 2 adaylari (fine-tune'suz) - Qwen3 0.6B ve 1.7B, GGUF Q4_K_M.
# Not: Model surumleri hizli degisiyor; kurulum gunu Hugging Face'te bu boyut
# sinifindaki guncel surumlere bak (MIMARI 3.7). Gerekirse URL'leri degistir.
set -euo pipefail
source "$(dirname "$0")/ortam.sh"
mkdir -p "$MODEL_DIR"
declare -A MODELLER=(
  [qwen3-0.6b-q4_k_m.gguf]="https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf"
  [qwen3-1.7b-q4_k_m.gguf]="https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf"
)
for ad in "${!MODELLER[@]}"; do
  hedef="$MODEL_DIR/$ad"
  if [ -s "$hedef" ]; then echo "var: $hedef"; continue; fi
  echo ">>> indiriliyor: $ad"
  curl -L --fail -o "$hedef.part" "${MODELLER[$ad]}" && mv "$hedef.part" "$hedef"
done
ls -lh "$MODEL_DIR"
