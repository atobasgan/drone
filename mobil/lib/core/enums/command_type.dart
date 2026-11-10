/// Desteklenen sesli komut tiplerini tanımlayan enum.
/// Her komut tipi bir Twist mesajı üretir.
enum CommandType {
  /// Kalkış — linear.z = +1.0
  takeoff,

  /// İniş — linear.z = -0.5
  land,

  /// İleri git — linear.x = +step
  forward,

  /// Geri git — linear.x = -step
  backward,

  /// Sola git (strafe) — linear.y = +step
  left,

  /// Sağa git (strafe) — linear.y = -step
  right,

  /// Yukarı çık — linear.z = +step
  up,

  /// Aşağı in — linear.z = -step
  down,

  /// Sola dön (yaw) — angular.z = +step
  rotateLeft,

  /// Sağa dön (yaw) — angular.z = -step
  rotateRight,

  /// Dur — tüm hızlar sıfır
  stop,

  /// Hızlan — adım değerini artır
  speedUp,

  /// Yavaşla — adım değerini azalt
  slowDown,

  /// Bilinmeyen komut
  unknown,
}

/// CommandType için yardımcı extension
extension CommandTypeExtension on CommandType {
  /// Komutun Türkçe açıklaması
  String get description {
    switch (this) {
      case CommandType.takeoff:
        return 'Kalkış';
      case CommandType.land:
        return 'İniş';
      case CommandType.forward:
        return 'İleri';
      case CommandType.backward:
        return 'Geri';
      case CommandType.left:
        return 'Sol';
      case CommandType.right:
        return 'Sağ';
      case CommandType.up:
        return 'Yukarı';
      case CommandType.down:
        return 'Aşağı';
      case CommandType.rotateLeft:
        return 'Sola Dön';
      case CommandType.rotateRight:
        return 'Sağa Dön';
      case CommandType.stop:
        return 'Dur';
      case CommandType.speedUp:
        return 'Hızlan';
      case CommandType.slowDown:
        return 'Yavaşla';
      case CommandType.unknown:
        return 'Bilinmeyen Komut';
    }
  }

  /// Komut hareket komutu mu? (Twist mesajı üretir)
  bool get isMovementCommand =>
      this != CommandType.speedUp &&
      this != CommandType.slowDown &&
      this != CommandType.unknown;

  /// Komut hız ayar komutu mu?
  bool get isSpeedCommand =>
      this == CommandType.speedUp || this == CommandType.slowDown;
}
