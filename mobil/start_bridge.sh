#!/usr/bin/env bash
# ==============================================================================
# DroneVoice - ROS 2 <-> Mobil Uygulama WebSocket Köprüsü Başlatıcı
# ==============================================================================
# Bu betik, mobil uygulamanın (Flutter) sim-drone Gazebo simülasyonuna
# Wi-Fi / yerel ağ üzerinden bağlanabilmesini sağlayan rosbridge WebSocket
# sunucusunu başlatır.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ROS 2 Jazzy ortamını yükle
if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
fi

echo "=================================================="
echo "    DRONEVOICE WEBSOCKET KÖPRÜSÜ BAŞLATILIYOR"
echo "=================================================="

# Yerel IP adresini bul ve ekrana yazdır
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "📱 Mobil Uygulamaya Girilecek IP : $LOCAL_IP"
echo "🔌 WebSocket Port                 : 9090"
echo "🛰️ WebSocket URL                 : ws://$LOCAL_IP:9090"
echo "=================================================="
echo "Komut kanalı     : /drone/cmd_vel (geometry_msgs/Twist)"
echo "Odometri kanalı  : /drone/odometry (nav_msgs/Odometry)"
echo "IMU kanalı       : /drone/imu (sensor_msgs/Imu)"
echo "=================================================="

# rosbridge_server paketinin kurulu olup olmadığını kontrol et
if ! ros2 pkg list 2>/dev/null | grep -q "rosbridge_server"; then
    echo "⚠️ 'rosbridge_server' paketi bulunamadı!"
    echo "Yüklemek için şu komutu çalıştırabilirsiniz:"
    echo "  sudo apt install -y ros-jazzy-rosbridge-suite"
    echo ""
    echo "Alternatif: Python tabanlı hafif websocket köprüsü başlatılıyor..."
    python3 "$SCRIPT_DIR/scripts/mobile_ws_bridge.py"
    exit 0
fi

# rosbridge_websocket düğümünü başlat
ros2 run rosbridge_server rosbridge_websocket --ros-args -p port:=9090

