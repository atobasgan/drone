/// ROS 2 ve rosbridge WebSocket bağlantı sabitleri.
/// Topic isimleri ve mesaj tipleri sim-drone projesindeki değerlerle
/// birebir eşleşmelidir.
class RosConstants {
  RosConstants._();

  // ── WebSocket / rosbridge Ayarları ──
  /// Varsayılan rosbridge WebSocket portu
  static const int defaultPort = 9090;

  /// Varsayılan WebSocket protokolü
  static const String wsProtocol = 'ws';

  /// Varsayılan host (aynı ağdaki ROS 2 bilgisayarının IP'si)
  static const String defaultHost = '192.168.1.100';

  /// Tam varsayılan WebSocket URL
  static String get defaultWsUrl => '$wsProtocol://$defaultHost:$defaultPort';

  // ── Topic İsimleri (sim-drone ile birebir uyumlu) ──
  /// Drone hız komut topic'i — geometry_msgs/msg/Twist
  static const String cmdVelTopic = '/drone/cmd_vel';

  /// Drone odometri topic'i — nav_msgs/msg/Odometry
  static const String odometryTopic = '/drone/odometry';

  /// Drone IMU topic'i — sensor_msgs/msg/Imu
  static const String imuTopic = '/drone/imu';

  /// Drone kamera ham görüntü topic'i
  static const String cameraImageTopic = '/drone/camera/image_raw';

  // ── Mesaj Tipleri ──
  static const String twistMsgType = 'geometry_msgs/msg/Twist';
  static const String odometryMsgType = 'nav_msgs/msg/Odometry';
  static const String imuMsgType = 'sensor_msgs/msg/Imu';
  static const String imageMsgType = 'sensor_msgs/msg/Image';

  // Uyumluluk alias'ları
  static const String cmdVelType = twistMsgType;
  static const String odometryType = odometryMsgType;
  static const String imuType = imuMsgType;
  static const String imageType = imageMsgType;

  // ── Yayınlama Hızı ──
  /// cmd_vel yayınlama hızı (Hz)
  static const int publishRateHz = 10;

  /// Yayınlama periyodu (milisaniye)
  static int get publishPeriodMs => (1000 / publishRateHz).round();

  // ── rosbridge Protokol Sabitleri ──
  /// rosbridge mesaj operasyon tipleri
  static const String opAdvertise = 'advertise';
  static const String opUnadvertise = 'unadvertise';
  static const String opPublish = 'publish';
  static const String opSubscribe = 'subscribe';
  static const String opUnsubscribe = 'unsubscribe';

  /// Varsayılan sıkıştırma tipi (subscriber için)
  static const String compressionNone = 'none';
  static const String compressionPng = 'png';
}
