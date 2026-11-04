#!/usr/bin/env bash
# Faz 3 ses bagimliliklari: PortAudio, faster-whisper, Silero VAD (torch CPU), sounddevice.
#   ./scripts/ses_kur.sh                 # + STT modelini (small) onceden indir
#   STT_MODELLER="small large-v3-turbo" ./scripts/ses_kur.sh
# Ubuntu'da sistem Python'una pip ile kurmak icin --break-system-packages gerekir
# (ROS 2 node'lari sistem Python'unu kullanir).
set -euo pipefail
PIP="python3 -m pip install --user --break-system-packages"

if command -v apt >/dev/null; then
  sudo apt install -y libportaudio2 portaudio19-dev python3-numpy
fi
# torch'un CPU surumu (CUDA'li varsayilan teker ~2 GB); VAD icin yeterli.
$PIP torch --index-url https://download.pytorch.org/whl/cpu
$PIP faster-whisper silero-vad sounddevice

for m in ${STT_MODELLER:-small}; do
  echo ">>> STT modeli indiriliyor: $m"
  python3 -c "from faster_whisper import WhisperModel; WhisperModel('$m', device='cpu', compute_type='int8')"
done
python3 -c "from silero_vad import load_silero_vad; load_silero_vad(); print('Silero VAD hazir')"
python3 -m sounddevice
