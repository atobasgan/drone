/// Uygulama genelinde kullanılan statik değerler.
///
/// Bu sınıf hız, mesafe ya da yön değeri içermez ve hesaplama yapmaz: hız
/// sınırları ve güvenlik kontrolleri backend'dedir (mission_executor/safety.py).
class AppConstants {
  AppConstants._();

  // ── Uygulama Bilgileri ──
  static const String appName = 'Drone Sesli Kontrol';
  static const String appVersion = '1.0.0';

  // ── Hızlı Komut Düğmeleri ──
  /// (etiket, gönderilecek ham metin). Metin, konuşulmuş gibi `/voice/text`
  /// konusuna olduğu gibi gönderilir; anlamı backend'in hızlı yolu belirler.
  static const List<(String, String)> quickCommands = [
    ('🚀 Kalkış', 'kalk'),
    ('⏫ 10 m Yüksel', '10 metre yüksel'),
    ('⏬ 10 m Alçal', '10 metre alçal'),
    ('⬆️ İleri 10 m', 'ileri 10 metre git'),
    ('⬇️ Geri 10 m', 'geri 10 metre git'),
    ('↩️ Sola Dön', 'sola dön'),
    ('↪️ Sağa Dön', 'sağa dön'),
    ('🏠 Eve Dön', 'eve dön'),
    ('🛬 İniş', 'in'),
    ('🛑 Dur', 'dur'),
  ];

  /// DURDUR düğmesinin gönderdiği metin. command_parser'da acil kelimedir:
  /// LLM'i beklemeden kuyruğu boşaltır.
  static const String emergencyStopText = 'dur';

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
