/// DroneCommand - Drone'a gönderilecek hareket komutunu temsil eden entity.
///
/// ROS 2 `/drone/cmd_vel` topic'ine gönderilen geometry_msgs/Twist
/// mesaj formatına doğrudan eşlenir.
/// Lineer hızlar m/s, açısal hızlar rad/s cinsindendir.
library;

/// Komut türlerini tanımlayan enum.
/// Her komut türü, drone'un farklı bir hareket moduna karşılık gelir.
enum DroneCommandType {
  /// İleri hareket (linear.x > 0)
  moveForward,

  /// Geri hareket (linear.x < 0)
  moveBackward,

  /// Sola hareket (linear.y > 0)
  moveLeft,

  /// Sağa hareket (linear.y < 0)
  moveRight,

  /// Yukarı hareket / yükselme (linear.z > 0)
  moveUp,

  /// Aşağı hareket / alçalma (linear.z < 0)
  moveDown,

  /// Sola dönüş (angular.z > 0)
  rotateLeft,

  /// Sağa dönüş (angular.z < 0)
  rotateRight,

  /// Durma / havada asılı kalma (tüm hızlar sıfır)
  hover,

  /// Özel / bileşik komut
  custom,
}

/// Drone hareket komutunu temsil eden temel entity sınıfı.
///
/// Twist mesaj yapısına doğrudan karşılık gelir:
/// - `linearX`, `linearY`, `linearZ` → `linear.x`, `linear.y`, `linear.z`
/// - `angularZ` → `angular.z`
///
/// Hız limitleri:
/// - Lineer XY: max ±3.0 m/s, adım 0.5 m/s
/// - Lineer Z:  max ±2.5 m/s, adım 0.5 m/s
/// - Açısal Z:  max ±2.0 rad/s, adım 0.5 rad/s
class DroneCommand {
  /// Komutun türü (ileri, geri, dur vs.)
  final DroneCommandType commandType;

  /// X ekseninde lineer hız (m/s) — ileri(+) / geri(-)
  final double linearX;

  /// Y ekseninde lineer hız (m/s) — sol(+) / sağ(-)
  final double linearY;

  /// Z ekseninde lineer hız (m/s) — yukarı(+) / aşağı(-)
  final double linearZ;

  /// Z ekseninde açısal hız (rad/s) — sola dön(+) / sağa dön(-)
  final double angularZ;

  /// Komutun oluşturulma zamanı
  final DateTime timestamp;

  const DroneCommand({
    required this.commandType,
    this.linearX = 0.0,
    this.linearY = 0.0,
    this.linearZ = 0.0,
    this.angularZ = 0.0,
    required this.timestamp,
  });

  /// Tüm hızların sıfır olduğu "dur/hover" komutu oluşturur.
  factory DroneCommand.hover() => DroneCommand(
        commandType: DroneCommandType.hover,
        timestamp: DateTime.now(),
      );

  /// Komutun tüm hız değerlerinin sıfır olup olmadığını kontrol eder.
  bool get isHover =>
      linearX == 0.0 &&
      linearY == 0.0 &&
      linearZ == 0.0 &&
      angularZ == 0.0;

  @override
  String toString() =>
      'DroneCommand($commandType, linear: [$linearX, $linearY, $linearZ], '
      'angular: [0.0, 0.0, $angularZ])';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DroneCommand &&
          commandType == other.commandType &&
          linearX == other.linearX &&
          linearY == other.linearY &&
          linearZ == other.linearZ &&
          angularZ == other.angularZ;

  @override
  int get hashCode => Object.hash(commandType, linearX, linearY, linearZ, angularZ);
}
