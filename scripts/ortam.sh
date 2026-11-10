# Ortak ayarlar. Diger betikler bunu "source" eder; istersen ~/.bashrc'ye de ekle.
# Degerleri kendi makinene gore degistir (ya da calistirmadan once export et).

export LLM_DRONE_DIR="${LLM_DRONE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export ROS_DISTRO="${ROS_DISTRO:-lyrical}"
export PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
export XRCE_AGENT_DIR="${XRCE_AGENT_DIR:-$HOME/Micro-XRCE-DDS-Agent}"
export LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
export MODEL_DIR="${MODEL_DIR:-$LLM_DRONE_DIR/models}"
# Faz 4: kendi fine-tune'lu modelin (finetune/README.md). FT=1 ile hepsini_baslat.sh bunu kullanir.
# Q8_0: olcumde Q4_K_M kadar dogru, yanlis kabulu daha dusuk ve bu CPU'da daha hizliydi.
# GPU'lu makinede ikisini finetune/eval/model_olc.sh ile olc; esitse kucuk olani (q4_k_m) sec.
export FT_MODEL="${FT_MODEL:-$LLM_DRONE_DIR/finetune/models/drone-0.6b/drone-0.6b-q8_0.gguf}"

# Simulasyonun gercek koordinatta baslamasi (Gorev 0.6): Ankara, Kizilay
export PX4_HOME_LAT="${PX4_HOME_LAT:-39.9208}"
export PX4_HOME_LON="${PX4_HOME_LON:-32.8541}"
export PX4_HOME_ALT="${PX4_HOME_ALT:-850}"

# PX4 ile uyumlu px4_msgs dali: PX4 hangi surumse ayni release dali (ornek: release/1.16)
export PX4_VERSION="${PX4_VERSION:-main}"
export PX4_MSGS_BRANCH="${PX4_MSGS_BRANCH:-$PX4_VERSION}"

ros_kaynakla() {
  # shellcheck disable=SC1090
  source "/opt/ros/$ROS_DISTRO/setup.bash"
  if [ -f "$LLM_DRONE_DIR/ros2_ws/install/setup.bash" ]; then
    # shellcheck disable=SC1091
    source "$LLM_DRONE_DIR/ros2_ws/install/setup.bash"
  fi
}
