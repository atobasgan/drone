#!/usr/bin/env bash
# FAZ 0 kurulumu (Gorev 0.2 - 0.5). Ubuntu 26.04 icin yon gosterir; bir adim
# hata verirse resmi dokumandaki guncel komutu kullan (YOL_HARITASI.txt).
#
#   ./scripts/kurulum_faz0.sh            # hepsi
#   ./scripts/kurulum_faz0.sh ros px4    # sadece secilen adimlar
# Adimlar: ros, gazebo, px4, agent, workspace
set -euo pipefail
source "$(dirname "$0")/ortam.sh"

adim_ros() {
  echo ">>> [0.2] ROS 2 $ROS_DISTRO"
  sudo apt update && sudo apt install -y software-properties-common curl
  sudo add-apt-repository -y universe
  # ros-apt-source paketi depo anahtarini ve kaynagini ekler (docs.ros.org)
  local surum
  surum=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
          | grep -F '"tag_name"' | awk -F'"' '{print $4}')
  curl -L -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${surum}/ros2-apt-source_${surum}.$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")_all.deb"
  sudo dpkg -i /tmp/ros2-apt-source.deb
  sudo apt update
  sudo apt install -y "ros-$ROS_DISTRO-desktop" ros-dev-tools python3-pip python3-pytest python3-requests
  grep -q "/opt/ros/$ROS_DISTRO/setup.bash" ~/.bashrc || \
    echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> ~/.bashrc
}

adim_gazebo() {
  echo ">>> [0.3] Gazebo (ROS $ROS_DISTRO ile eslesen surum: Jetty) + ros_gz"
  sudo apt install -y "ros-$ROS_DISTRO-ros-gz"
  gz sim --version || true
}

adim_px4() {
  echo ">>> [0.4] PX4-Autopilot ($PX4_VERSION)"
  if [ ! -d "$PX4_DIR" ]; then
    git clone https://github.com/PX4/PX4-Autopilot.git --recursive -b "$PX4_VERSION" "$PX4_DIR"
  fi
  bash "$PX4_DIR/Tools/setup/ubuntu.sh" --no-nuttx
  echo "PX4 bagimliliklari kuruldu. Oturumu kapatip ac, sonra:"
  echo "    cd $PX4_DIR && make px4_sitl gz_x500"
}

adim_agent() {
  echo ">>> [0.5] Micro XRCE-DDS Agent"
  if [ ! -d "$XRCE_AGENT_DIR" ]; then
    # PX4 dokumani belirli bir etiket oneriyorsa -b ile onu kullan
    git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git "$XRCE_AGENT_DIR"
  fi
  mkdir -p "$XRCE_AGENT_DIR/build"
  (cd "$XRCE_AGENT_DIR/build" && cmake .. && make -j"$(nproc)" && sudo make install)
  sudo ldconfig /usr/local/lib/
}

adim_workspace() {
  echo ">>> [0.5] ros2_ws: px4_msgs ($PX4_MSGS_BRANCH) + px4_ros_com + kendi paketlerimiz"
  local src="$LLM_DRONE_DIR/ros2_ws/src"
  [ -d "$src/px4_msgs" ] || git clone -b "$PX4_MSGS_BRANCH" https://github.com/PX4/px4_msgs.git "$src/px4_msgs"
  [ -d "$src/px4_ros_com" ] || git clone https://github.com/PX4/px4_ros_com.git "$src/px4_ros_com"
  "$(dirname "$0")/derle.sh"
}

if [ $# -eq 0 ]; then
  set -- ros gazebo px4 agent workspace
fi
for adim in "$@"; do
  "adim_$adim"
done
echo ">>> Bitti. NOTLAR.md'ye calisan surumleri yaz: ./scripts/surumleri_yaz.sh"
