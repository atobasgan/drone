/// SettingsRepository - Uygulama ayarları için soyut repository.
///
/// Domain katmanında tanımlanan bu arayüz, ayarların nerede ve nasıl
/// saklandığına dair hiçbir detay içermez. Uygulama detayları
/// data katmanındaki `SettingsRepositoryImpl` tarafından sağlanır.
library;

/// Güvenlik limit ayarlarını tutan sınıf.
///
/// Drone'un maksimum hız ve hareket sınırlarını belirler.
class SafetyLimits {
  /// Maksimum lineer XY hızı (m/s) — varsayılan: 3.0
  final double maxLinearXY;

  /// Maksimum lineer Z hızı (m/s) — varsayılan: 2.5
  final double maxLinearZ;

  /// Maksimum açısal Z hızı (rad/s) — varsayılan: 2.0
  final double maxAngularZ;

  /// Hız artış adımı (m/s veya rad/s) — varsayılan: 0.5
  final double speedStep;

  const SafetyLimits({
    this.maxLinearXY = 3.0,
    this.maxLinearZ = 2.5,
    this.maxAngularZ = 2.0,
    this.speedStep = 0.5,
  });

  /// Varsayılan güvenlik limitleri
  static const SafetyLimits defaults = SafetyLimits();

  @override
  String toString() =>
      'SafetyLimits(maxXY: $maxLinearXY, maxZ: $maxLinearZ, '
      'maxAngZ: $maxAngularZ, adım: $speedStep)';
}

/// Uygulama ayarları repository arayüzü.
///
/// Rosbridge bağlantı ayarları, dil tercihi, hız limitleri gibi
/// kullanıcı tercihlerini yönetir.
abstract class SettingsRepository {
  // ── Rosbridge Bağlantı Ayarları ──

  /// Rosbridge sunucusunun IP adresi veya hostname'ini döndürür.
  Future<String> getRosbridgeHost();

  /// Rosbridge sunucu adresini kaydeder.
  Future<void> setRosbridgeHost(String host);

  /// Rosbridge sunucusunun port numarasını döndürür.
  Future<int> getRosbridgePort();

  /// Rosbridge port numarasını kaydeder.
  Future<void> setRosbridgePort(int port);

  // ── Dil Ayarları ──

  /// Ses tanıma dilini döndürür (ör. "tr_TR").
  Future<String> getLanguage();

  /// Ses tanıma dilini kaydeder.
  Future<void> setLanguage(String language);

  // ── Hız Ayarları ──

  /// Kullanıcının belirlediği maksimum hızı döndürür (m/s).
  Future<double> getMaxSpeed();

  /// Maksimum hız değerini kaydeder.
  Future<void> setMaxSpeed(double speed);

  // ── Güvenlik Limitleri ──

  /// Güvenlik limit ayarlarını döndürür.
  Future<SafetyLimits> getSafetyLimits();

  /// Güvenlik limit ayarlarını kaydeder.
  Future<void> setSafetyLimits(SafetyLimits limits);
}
