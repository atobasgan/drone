/// Uygulama genelinde kullanılan sabit değerler.
/// Drone kontrol parametreleri sim-drone projesindeki değerlerle birebir uyumludur.
class AppConstants {
  AppConstants._();

  // ── Uygulama Bilgileri ──
  static const String appName = 'Drone Sesli Kontrol';
  static const String appVersion = '1.0.0';

  // ── Hız Parametreleri (sim-drone uyumlu) ──
  /// Her hız artış/azalış adımı (m/s veya rad/s)
  static const double speedStep = 0.5;

  /// Minimum hız adımı
  static const double minSpeedStep = 0.5;

  /// Maksimum hız adımı
  static const double maxSpeedStep = 3.0;

  /// Maksimum doğrusal hız XY ekseni (m/s)
  static const double maxLinearVelocityXY = 3.0;

  /// Maksimum doğrusal hız Z ekseni (m/s)
  static const double maxLinearVelocityZ = 2.5;

  /// Maksimum açısal hız (rad/s)
  static const double maxAngularVelocity = 2.0;

  // ── Kalkış / İniş Varsayılan Hızları ──
  /// Kalkış dikey hızı (m/s)
  static const double takeoffVelocityZ = 1.0;

  /// İniş dikey hızı (m/s) — negatif yön
  static const double landingVelocityZ = -0.5;

  // ── Ses Tanıma Ayarları ──
  /// Ses tanıma dili
  static const String speechLocale = 'tr_TR';

  /// Dinleme süresi (saniye)
  static const int listenDurationSeconds = 5;

  /// Ses seviyesi eşik değeri
  static const double soundLevelThreshold = -2.0;

  // ── TTS (Metin-Konuşma) Ayarları ──
  static const String ttsLanguage = 'tr-TR';
  static const double ttsSpeechRate = 0.5;
  static const double ttsVolume = 1.0;
  static const double ttsPitch = 1.0;

  // ── Bağlantı Ayarları ──
  /// WebSocket yeniden bağlanma denemesi bekleme süresi (ms)
  static const int reconnectDelayMs = 3000;

  /// Maksimum yeniden bağlanma denemesi sayısı
  static const int maxReconnectAttempts = 5;

  /// Bağlantı zaman aşımı (saniye)
  static const int connectionTimeoutSeconds = 10;

  // ── Titreşim Süreleri (ms) ──
  static const int vibrationShort = 50;
  static const int vibrationMedium = 100;
  static const int vibrationLong = 200;

  // ── UI Sabitleri ──
  static const double defaultPadding = 16.0;
  static const double defaultBorderRadius = 12.0;
  static const double joystickSize = 200.0;
}
