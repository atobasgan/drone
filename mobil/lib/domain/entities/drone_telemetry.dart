/// DroneTelemetry - Drone'dan gelen telemetri verilerini temsil eden entity.
///
/// İki farklı ROS 2 topic'inden gelen verileri birleştirir:
/// - `/drone/odometry` (nav_msgs/Odometry): konum ve hız bilgileri
/// - `/drone/imu` (sensor_msgs/Imu): ivmeölçer ve jiroskop verileri
library;

/// 3 boyutlu vektör (konum veya hız için)
class Vector3 {
  final double x;
  final double y;
  final double z;

  const Vector3({
    this.x = 0.0,
    this.y = 0.0,
    this.z = 0.0,
  });

  static const zero = Vector3(x: 0.0, y: 0.0, z: 0.0);

  @override
  String toString() => 'Vector3(x: $x, y: $y, z: $z)';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Vector3 &&
          runtimeType == other.runtimeType &&
          x == other.x &&
          y == other.y &&
          z == other.z;

  @override
  int get hashCode => x.hashCode ^ y.hashCode ^ z.hashCode;
}

/// Drone'un anlık telemetri verilerini tutan entity sınıfı.
///
/// Odometry'den alınan değerler:
/// - [positionX], [positionY], [positionZ]: Drone'un 3D konumu (metre)
/// - [velocityX], [velocityY], [velocityZ]: Drone'un lineer hızları (m/s)
///
/// IMU'dan alınan değerler:
/// - [roll]: X ekseni etrafında dönüş açısı (radyan)
/// - [pitch]: Y ekseni etrafında dönüş açısı (radyan)
/// - [yaw]: Z ekseni etrafında dönüş açısı (radyan)
class DroneTelemetry {
  // ── Konum bilgileri (Odometry'den) ──

  /// X eksenindeki konum (metre)
  final double positionX;

  /// Y eksenindeki konum (metre)
  final double positionY;

  /// Z eksenindeki konum / yükseklik (metre)
  final double positionZ;

  // ── Hız bilgileri (Odometry'den) ──

  /// X eksenindeki lineer hız (m/s)
  final double velocityX;

  /// Y eksenindeki lineer hız (m/s)
  final double velocityY;

  /// Z eksenindeki lineer hız (m/s)
  final double velocityZ;

  // ── Oryantasyon bilgileri (IMU'dan) ──

  /// Yaw açısı — Z ekseni etrafında dönüş (radyan)
  final double yaw;

  /// Roll açısı — X ekseni etrafında dönüş (radyan)
  final double roll;

  /// Pitch açısı — Y ekseni etrafında dönüş (radyan)
  final double pitch;

  /// Dönüş hızı / açısal hız (rad/s)
  final double yawRate;

  /// Telemetri verisinin zaman damgası
  final DateTime timestamp;

  const DroneTelemetry({
    this.positionX = 0.0,
    this.positionY = 0.0,
    this.positionZ = 0.0,
    this.velocityX = 0.0,
    this.velocityY = 0.0,
    this.velocityZ = 0.0,
    this.yaw = 0.0,
    this.roll = 0.0,
    this.pitch = 0.0,
    this.yawRate = 0.0,
    required this.timestamp,
  });

  /// 3D Konum vektörü
  Vector3 get position => Vector3(x: positionX, y: positionY, z: positionZ);

  /// 3D Lineer hız vektörü
  Vector3 get velocity => Vector3(x: velocityX, y: velocityY, z: velocityZ);

  /// Pusula açısı / heading (derece cinsinden: 0 - 360)
  double get heading => ((yaw * 180.0 / 3.141592653589793) % 360.0 + 360.0) % 360.0;

  /// Sıfır değerlerle başlangıç telemetrisi oluşturur.
  factory DroneTelemetry.initial() => DroneTelemetry(
        timestamp: DateTime.now(),
      );

  /// Drone'un yerden yüksekliği (metre) — positionZ ile aynıdır.
  double get altitude => positionZ;

  /// Drone'un toplam yatay hızı (m/s).
  double get horizontalSpeed {
    return _sqrt(velocityX * velocityX + velocityY * velocityY);
  }

  /// Drone'un toplam 3D hızı (m/s).
  double get totalSpeed {
    return _sqrt(
      velocityX * velocityX +
          velocityY * velocityY +
          velocityZ * velocityZ,
    );
  }

  /// Basit karekök hesabı (dart:math importu olmadan domain katmanı saf kalır).
  static double _sqrt(double value) {
    if (value <= 0) return 0.0;
    double guess = value / 2;
    for (int i = 0; i < 20; i++) {
      guess = (guess + value / guess) / 2;
    }
    return guess;
  }

  /// Mevcut telemetriyi kısmen güncelleyerek yeni bir kopya oluşturur.
  DroneTelemetry copyWith({
    double? positionX,
    double? positionY,
    double? positionZ,
    double? velocityX,
    double? velocityY,
    double? velocityZ,
    double? yaw,
    double? roll,
    double? pitch,
    double? yawRate,
    DateTime? timestamp,
  }) {
    return DroneTelemetry(
      positionX: positionX ?? this.positionX,
      positionY: positionY ?? this.positionY,
      positionZ: positionZ ?? this.positionZ,
      velocityX: velocityX ?? this.velocityX,
      velocityY: velocityY ?? this.velocityY,
      velocityZ: velocityZ ?? this.velocityZ,
      yaw: yaw ?? this.yaw,
      roll: roll ?? this.roll,
      pitch: pitch ?? this.pitch,
      yawRate: yawRate ?? this.yawRate,
      timestamp: timestamp ?? this.timestamp,
    );
  }

  @override
  String toString() =>
      'DroneTelemetry(pos: [$positionX, $positionY, $positionZ], '
      'vel: [$velocityX, $velocityY, $velocityZ], '
      'orient: [roll=$roll, pitch=$pitch, yaw=$yaw])';
}
