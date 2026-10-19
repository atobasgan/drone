#!/usr/bin/env bash
# Gorev 2.3: llama.cpp'yi derle (GPU varsa CUDA ile).
set -euo pipefail
source "$(dirname "$0")/ortam.sh"
sudo apt install -y build-essential cmake git libcurl4-openssl-dev
[ -d "$LLAMA_CPP_DIR" ] || git clone https://github.com/ggml-org/llama.cpp.git "$LLAMA_CPP_DIR"
cd "$LLAMA_CPP_DIR"
if command -v nvidia-smi >/dev/null 2>&1; then
  echo ">>> GPU bulundu, CUDA ile derleniyor"
  cmake -B build -DGGML_CUDA=ON
else
  echo ">>> GPU yok, CPU icin derleniyor"
  cmake -B build
fi
cmake --build build --config Release -j"$(nproc)" --target llama-server llama-cli
echo ">>> $LLAMA_CPP_DIR/build/bin/llama-server hazir"
