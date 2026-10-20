#!/usr/bin/env bash
# ==============================================================================
# DroneVoice - ROS 2 <-> Mobil Uygulama WebSocket Köprüsü Başlatıcı
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ROS 2 Jazzy ortamını yükle
if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
fi

echo "=================================================="
echo "    DRONEVOICE WEBSOCKET KÖPRÜSÜ BAŞLATILIYOR"
echo "=================================================="

# Yerel IP adresini bul
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "📱 Mobil Uygulamaya Girilecek IP : $LOCAL_IP"
echo "🔌 WebSocket Port                 : 9090"
echo "🛰️ WebSocket URL                 : ws://$LOCAL_IP:9090"
echo "=================================================="
echo "Hedef Topic: /drone/cmd_vel (geometry_msgs/Twist)"
echo "=================================================="

# rosbridge_server varsa onu kullan, yoksa dahili sıfır bağımlılıklı Python köprüsünü başlat
if ros2 pkg list 2>/dev/null | grep -q "rosbridge_server"; then
    echo "✅ ROS 2 rosbridge_server bulundu, başlatılıyor..."
    ros2 run rosbridge_server rosbridge_websocket --ros-args -p port:=9090
else
    echo "⚡ ROS 2 rosbridge paketi kurulu değil."
    echo "🚀 Dahili sıfır bağımlılıklı köprü başlatılıyor..."
    python3 "$SCRIPT_DIR/scripts/mobile_ws_bridge.py"
fi
