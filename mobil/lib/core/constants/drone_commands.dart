import '../enums/command_type.dart';
import 'app_constants.dart';

/// Tek bir drone komutu — linear ve angular hız bileşenlerini içerir.
/// sim-drone'un geometry_msgs/msg/Twist formatına birebir uyumludur.
///
/// Twist mesaj yapısı:
/// ```
/// linear:
///   x: ileri(+) / geri(-)
///   y: sol(+) / sağ(-)
///   z: yukarı(+) / aşağı(-)
/// angular:
///   x: 0.0 (kullanılmıyor)
///   y: 0.0 (kullanılmıyor)
///   z: sola_dön(+) / sağa_dön(-)
/// ```
class DroneCommand {
  final CommandType type;
  final double linearX;   // İleri(+) / Geri(-)
  final double linearY;   // Sol(+) / Sağ(-)
  final double linearZ;   // Yukarı(+) / Aşağı(-)
  final double angularX;  // Kullanılmıyor — her zaman 0
  final double angularY;  // Kullanılmıyor — her zaman 0
  final double angularZ;  // Sola dön(+) / Sağa dön(-)

  const DroneCommand({
    required this.type,
    this.linearX = 0.0,
    this.linearY = 0.0,
    this.linearZ = 0.0,
    this.angularX = 0.0,
    this.angularY = 0.0,
    this.angularZ = 0.0,
  });

  /// Komutu rosbridge Twist mesajı formatına dönüştür
  Map<String, dynamic> toTwistMsg() {
    return {
      'linear': {
        'x': linearX,
        'y': linearY,
        'z': linearZ,
      },
      'angular': {
        'x': angularX,
        'y': angularY,
        'z': angularZ,
      },
    };
  }

  /// Dur komutu (tüm hızlar sıfır)
  static const DroneCommand stop = DroneCommand(type: CommandType.stop);

  @override
  String toString() =>
      'DroneCommand(${type.description}: '
      'lin[x:$linearX, y:$linearY, z:$linearZ] '
      'ang[z:$angularZ])';
}

/// Türkçe sesli komutları DroneCommand nesnelerine dönüştüren sınıf.
/// Tüm komutlar sim-drone'un beklediği Twist formatıyla uyumludur.
class DroneCommands {
  DroneCommands._();

  /// Sesli komut anahtar kelimelerini CommandType'a eşleyen harita.
  /// Anahtar kelimeler küçük harfle tutulur, eşleştirme sırasında
  /// kullanıcı girdisi de küçük harfe dönüştürülür.
  static const Map<String, CommandType> _voiceCommandMap = {
    // Kalkış komutları
    'kalkış': CommandType.takeoff,
    'kalk': CommandType.takeoff,
    'havaları': CommandType.takeoff,
    'havalan': CommandType.takeoff,

    // İniş komutları
    'iniş': CommandType.land,
    'in': CommandType.land,
    'yer': CommandType.land,
    'iniş yap': CommandType.land,

    // Yön komutları
    'ileri': CommandType.forward,
    'ileri git': CommandType.forward,
    'geri': CommandType.backward,
    'geri git': CommandType.backward,
    'sol': CommandType.left,
    'sola': CommandType.left,
    'sola git': CommandType.left,
    'sağ': CommandType.right,
    'sağa': CommandType.right,
    'sağa git': CommandType.right,
    'yukarı': CommandType.up,
    'yukarı çık': CommandType.up,
    'aşağı': CommandType.down,
    'aşağı in': CommandType.down,

    // Dönüş komutları
    'sola dön': CommandType.rotateLeft,
    'sola döndür': CommandType.rotateLeft,
    'sağa dön': CommandType.rotateRight,
    'sağa döndür': CommandType.rotateRight,

    // Dur komutu
    'dur': CommandType.stop,
    'durdur': CommandType.stop,
    'bekle': CommandType.stop,

    // Hız komutları
    'hızlan': CommandType.speedUp,
    'hız artır': CommandType.speedUp,
    'daha hızlı': CommandType.speedUp,
    'yavaşla': CommandType.slowDown,
    'hız azalt': CommandType.slowDown,
    'daha yavaş': CommandType.slowDown,
  };

  /// Ses metninden CommandType belirle.
  /// Girdi küçük harfe çevrilerek eşleştirilir.
  static CommandType parseVoiceCommand(String voiceText) {
    final normalized = voiceText.trim().toLowerCase();

    // Önce tam eşleşme dene
    if (_voiceCommandMap.containsKey(normalized)) {
      return _voiceCommandMap[normalized]!;
    }

    // Tam eşleşme yoksa, içerme (contains) kontrolü yap
    // Uzun ifadeler önce kontrol edilir (en spesifik eşleşme)
    final sortedKeys = _voiceCommandMap.keys.toList()
      ..sort((a, b) => b.length.compareTo(a.length));

    for (final key in sortedKeys) {
      if (normalized.contains(key)) {
        return _voiceCommandMap[key]!;
      }
    }

    return CommandType.unknown;
  }

  /// CommandType ve mevcut hız adımına göre DroneCommand oluştur.
  /// [step] parametresi mevcut hız adımıdır (varsayılan: 0.5 m/s).
  static DroneCommand createCommand(CommandType type, {double? step}) {
    final currentStep = step ?? AppConstants.speedStep;

    switch (type) {
      case CommandType.takeoff:
        return const DroneCommand(
          type: CommandType.takeoff,
          linearZ: AppConstants.takeoffVelocityZ, // +1.0 m/s yukarı
        );

      case CommandType.land:
        return const DroneCommand(
          type: CommandType.land,
          linearZ: AppConstants.landingVelocityZ, // -0.5 m/s aşağı
        );

      case CommandType.forward:
        return DroneCommand(
          type: CommandType.forward,
          linearX: currentStep, // +step ileri
        );

      case CommandType.backward:
        return DroneCommand(
          type: CommandType.backward,
          linearX: -currentStep, // -step geri
        );

      case CommandType.left:
        return DroneCommand(
          type: CommandType.left,
          linearY: currentStep, // +step sol (strafe)
        );

      case CommandType.right:
        return DroneCommand(
          type: CommandType.right,
          linearY: -currentStep, // -step sağ (strafe)
        );

      case CommandType.up:
        return DroneCommand(
          type: CommandType.up,
          linearZ: currentStep, // +step yukarı
        );

      case CommandType.down:
        return DroneCommand(
          type: CommandType.down,
          linearZ: -currentStep, // -step aşağı
        );

      case CommandType.rotateLeft:
        return DroneCommand(
          type: CommandType.rotateLeft,
          angularZ: currentStep, // +step sola dön (yaw)
        );

      case CommandType.rotateRight:
        return DroneCommand(
          type: CommandType.rotateRight,
          angularZ: -currentStep, // -step sağa dön (yaw)
        );

      case CommandType.stop:
        return DroneCommand.stop;

      case CommandType.speedUp:
        // Hız artırma — komut olarak dur gönder, step artışı BLoC'ta yönetilir
        return DroneCommand.stop;

      case CommandType.slowDown:
        // Hız azaltma — komut olarak dur gönder, step azalışı BLoC'ta yönetilir
        return DroneCommand.stop;

      case CommandType.unknown:
        return DroneCommand.stop;
    }
  }

  /// Sesli metni doğrudan DroneCommand'a dönüştür.
  /// Kısa yol: parse + create
  static DroneCommand fromVoice(String voiceText, {double? step}) {
    final type = parseVoiceCommand(voiceText);
    return createCommand(type, step: step);
  }

  /// Mevcut hız adımını artır (clamp ile sınırla)
  static double increaseSpeed(double currentStep) {
    final newStep = currentStep + AppConstants.speedStep;
    return newStep.clamp(AppConstants.minSpeedStep, AppConstants.maxSpeedStep);
  }

  /// Mevcut hız adımını azalt (clamp ile sınırla)
  static double decreaseSpeed(double currentStep) {
    final newStep = currentStep - AppConstants.speedStep;
    return newStep.clamp(AppConstants.minSpeedStep, AppConstants.maxSpeedStep);
  }

  /// Hız değerini maksimum sınırla kısıtla
  static double clampLinearXY(double velocity) {
    return velocity.clamp(
      -AppConstants.maxLinearVelocityXY,
      AppConstants.maxLinearVelocityXY,
    );
  }

  static double clampLinearZ(double velocity) {
    return velocity.clamp(
      -AppConstants.maxLinearVelocityZ,
      AppConstants.maxLinearVelocityZ,
    );
  }

  static double clampAngularZ(double velocity) {
    return velocity.clamp(
      -AppConstants.maxAngularVelocity,
      AppConstants.maxAngularVelocity,
    );
  }
}

/// Geriye dönük uyumluluk için alias
typedef DroneCommandMap = DroneCommands;
