/// ProcessVoiceCommand - Sesli komutu ayrıştırma ve DroneCommand'a dönüştürme use case'i.
///
/// Kullanıcının Türkçe sesli komutunu regex kalıplarıyla eşleştirerek
/// uygun drone hareketine çevirir. keyboard_teleop.py ile birebir
/// aynı hareket mantığını uygular:
///
/// | Sesli Komut               | Hareket            | Değer                  |
/// |---------------------------|--------------------|------------------------|
/// | "ileri"                   | linear.x += 0.5   | max +3.0 m/s           |
/// | "geri"                    | linear.x -= 0.5   | max -3.0 m/s           |
/// | "sol"                     | linear.y += 0.5   | max +3.0 m/s           |
/// | "sağ"                     | linear.y -= 0.5   | max -3.0 m/s           |
/// | "yukarı/yüksel/kalkış"    | linear.z += 0.5   | max +2.5 m/s           |
/// | "aşağı/alçal/iniş"       | linear.z -= 0.5   | max -2.5 m/s           |
/// | "sola dön"                | angular.z += 0.5  | max +2.0 rad/s         |
/// | "sağa dön"                | angular.z -= 0.5  | max -2.0 rad/s         |
/// | "dur/bekle"               | tüm değerler = 0  | hover                  |
library;

import '../entities/drone_command.dart';
import '../entities/voice_command.dart';
import '../repositories/settings_repository.dart';

/// Sesli komutu işleyen use case sınıfı.
///
/// Gelen ham metni Türkçe regex kalıplarıyla eşleştirir ve
/// uygun [DroneCommand] nesnesine dönüştürür.
class ProcessVoiceCommand {
  /// Güvenlik limitlerine erişmek için ayarlar repository'si
  final SettingsRepository _settingsRepository;

  ProcessVoiceCommand(this._settingsRepository);

  /// Mevcut hız durumunu takip etmek için kullanılan değişkenler.
  /// keyboard_teleop.py gibi kümülatif (birikimli) çalışır:
  /// Her komut mevcut hıza eklenir, "dur" komutu sıfırlar.
  double _currentLinearX = 0.0;
  double _currentLinearY = 0.0;
  double _currentLinearZ = 0.0;
  double _currentAngularZ = 0.0;

  /// Hız artış adımı (m/s veya rad/s)
  static const double _speedStep = 0.5;

  // ── Türkçe komut kalıpları (regex) ──

  /// Türkçe harflerle çalışan kelime sınırı.
  ///
  /// Dart'ta `\b` yalnızca ASCII harfleri tanır: "kalkış", "yukarı", "iniş"
  /// gibi ı/ş/ğ ile biten kelimelerde sınır bulunamıyor ve komut hiç
  /// eşleşmiyordu. Kalıplarda `\b` yazıp burada Unicode karşılığına çeviriyoruz.
  static const String _sinir =
      r'(?:(?<![\p{L}\p{N}])(?=[\p{L}\p{N}])|(?<=[\p{L}\p{N}])(?![\p{L}\p{N}]))';

  static RegExp _kalip(String kalip) => RegExp(
        kalip.replaceAll(r'\b', _sinir),
        caseSensitive: false,
        unicode: true,
      );

  /// Türkçe'ye uygun küçük harfe çevirme.
  ///
  /// Dart'ın `toLowerCase()`'i "İ"yi "i̇" (i + birleşik nokta) yapar ve
  /// tanıyıcının büyük harfle başlattığı "İleri git" eşleşmez; "I" da "ı"
  /// yerine "i" olur. Önce bu iki harfi elle çeviriyoruz.
  static String _turkceKucuk(String metin) =>
      metin.replaceAll('İ', 'i').replaceAll('I', 'ı').toLowerCase();

  /// İleri hareket kalıbı
  static final RegExp _forwardPattern = _kalip(
    r'\b(ileri|ileri\s+git|ileri\s+hareket)\b',
  );

  /// Geri hareket kalıbı
  static final RegExp _backwardPattern = _kalip(
    r'\b(geri|geri\s+git|geri\s+gel|geri\s+hareket)\b',
  );

  /// Sola hareket kalıbı (dönüş değil, yanal hareket)
  static final RegExp _leftPattern = _kalip(
    r'^sol$|^sola\s+git$|^sola\s+hareket$',
  );

  /// Sağa hareket kalıbı (dönüş değil, yanal hareket)
  static final RegExp _rightPattern = _kalip(
    r'^sa[gğ]$|^sa[gğ]a\s+git$|^sa[gğ]a\s+hareket$',
  );

  /// Yukarı hareket / yükselme kalıbı
  static final RegExp _upPattern = _kalip(
    r'\b(yukar[iıİ]|y[uü]ksel|kalk[iıİ][sş])\b',
  );

  /// Aşağı hareket / alçalma kalıbı
  static final RegExp _downPattern = _kalip(
    r'\b(a[sş]a[gğ][iıİ]|al[cç]al|ini[sş])\b',
  );

  /// Sola dönüş kalıbı
  static final RegExp _rotateLeftPattern = _kalip(
    r'\bsola\s+d[oö]n\b',
  );

  /// Sağa dönüş kalıbı
  static final RegExp _rotateRightPattern = _kalip(
    r'\bsa[gğ]a\s+d[oö]n\b',
  );

  /// Durma / hover kalıbı
  static final RegExp _hoverPattern = _kalip(
    r'\b(dur|bekle|stop|kal)\b',
  );

  /// Sesli komutu işler ve [VoiceCommand] döndürür.
  ///
  /// [rawText] parametresi ses tanıma motorundan gelen ham metindir.
  /// [confidence] parametresi tanıma güvenilirlik skorudur (0.0 – 1.0).
  Future<VoiceCommand> call({
    required String rawText,
    double confidence = 1.0,
  }) async {
    // Metni normalize et: küçük harfe çevir, kenarlardan boşlukları temizle
    final normalizedText = _turkceKucuk(rawText).trim();

    // Güvenlik limitlerini ayarlardan al
    final limits = await _settingsRepository.getSafetyLimits();

    // Komutu ayrıştır
    final droneCommand = _parseCommand(normalizedText, limits);

    // VoiceCommand nesnesi oluştur
    return VoiceCommand(
      rawText: rawText,
      confidence: confidence,
      parsedCommand: droneCommand,
      timestamp: DateTime.now(),
      isValid: droneCommand != null,
    );
  }

  /// Normalize edilmiş metni regex kalıplarıyla eşleştirip
  /// uygun [DroneCommand] nesnesine dönüştürür.
  ///
  /// Eşleşme bulunamazsa `null` döndürür.
  DroneCommand? _parseCommand(String text, SafetyLimits limits) {
    final maxXY = limits.maxLinearXY;
    final maxZ = limits.maxLinearZ;
    final maxAngZ = limits.maxAngularZ;

    // ── Dur / Hover komutu ──
    if (_hoverPattern.hasMatch(text)) {
      _currentLinearX = 0.0;
      _currentLinearY = 0.0;
      _currentLinearZ = 0.0;
      _currentAngularZ = 0.0;
      return DroneCommand(
        commandType: DroneCommandType.hover,
        linearX: 0.0,
        linearY: 0.0,
        linearZ: 0.0,
        angularZ: 0.0,
        timestamp: DateTime.now(),
      );
    }

    // ── Sola dönüş (yanal hareketten önce kontrol — "sola dön" vs "sol") ──
    if (_rotateLeftPattern.hasMatch(text)) {
      _currentAngularZ = _clamp(_currentAngularZ + _speedStep, -maxAngZ, maxAngZ);
      return _buildCommand(DroneCommandType.rotateLeft);
    }

    // ── Sağa dönüş ──
    if (_rotateRightPattern.hasMatch(text)) {
      _currentAngularZ = _clamp(_currentAngularZ - _speedStep, -maxAngZ, maxAngZ);
      return _buildCommand(DroneCommandType.rotateRight);
    }

    // ── İleri hareket ──
    if (_forwardPattern.hasMatch(text)) {
      _currentLinearX = _clamp(_currentLinearX + _speedStep, -maxXY, maxXY);
      return _buildCommand(DroneCommandType.moveForward);
    }

    // ── Geri hareket ──
    if (_backwardPattern.hasMatch(text)) {
      _currentLinearX = _clamp(_currentLinearX - _speedStep, -maxXY, maxXY);
      return _buildCommand(DroneCommandType.moveBackward);
    }

    // ── Sol hareket (yanal) ──
    if (_leftPattern.hasMatch(text)) {
      _currentLinearY = _clamp(_currentLinearY + _speedStep, -maxXY, maxXY);
      return _buildCommand(DroneCommandType.moveLeft);
    }

    // ── Sağ hareket (yanal) ──
    if (_rightPattern.hasMatch(text)) {
      _currentLinearY = _clamp(_currentLinearY - _speedStep, -maxXY, maxXY);
      return _buildCommand(DroneCommandType.moveRight);
    }

    // ── Yukarı / yüksel / kalkış ──
    if (_upPattern.hasMatch(text)) {
      _currentLinearZ = _clamp(_currentLinearZ + _speedStep, -maxZ, maxZ);
      return _buildCommand(DroneCommandType.moveUp);
    }

    // ── Aşağı / alçal / iniş ──
    if (_downPattern.hasMatch(text)) {
      _currentLinearZ = _clamp(_currentLinearZ - _speedStep, -maxZ, maxZ);
      return _buildCommand(DroneCommandType.moveDown);
    }

    // Tanınmayan komut
    return null;
  }

  /// Mevcut hız değerlerinden [DroneCommand] oluşturur.
  DroneCommand _buildCommand(DroneCommandType type) {
    return DroneCommand(
      commandType: type,
      linearX: _currentLinearX,
      linearY: _currentLinearY,
      linearZ: _currentLinearZ,
      angularZ: _currentAngularZ,
      timestamp: DateTime.now(),
    );
  }

  /// Bir değeri minimum ve maksimum arasında sınırlar.
  double _clamp(double value, double min, double max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
  }

  /// Mevcut hız durumunu sıfırlar.
  /// Yeni bir uçuş oturumu başlatırken kullanılır.
  void resetState() {
    _currentLinearX = 0.0;
    _currentLinearY = 0.0;
    _currentLinearZ = 0.0;
    _currentAngularZ = 0.0;
  }

  /// Mevcut hız değerlerini döndürür (debug/UI amaçlı).
  Map<String, double> get currentVelocities => {
        'linearX': _currentLinearX,
        'linearY': _currentLinearY,
        'linearZ': _currentLinearZ,
        'angularZ': _currentAngularZ,
      };
}
