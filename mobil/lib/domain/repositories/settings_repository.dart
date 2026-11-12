/// SettingsRepository - Uygulama ayarları için soyut repository.
///
/// Domain katmanında tanımlanan bu arayüz, ayarların nerede ve nasıl
/// saklandığına dair hiçbir detay içermez. Uygulama detayları
/// data katmanındaki `SettingsRepositoryImpl` tarafından sağlanır.
library;

/// Uygulama ayarları repository arayüzü.
///
/// Rosbridge bağlantı ayarları ve dil tercihini yönetir. Hız ve güvenlik
/// limitleri mobil uygulamada tutulmaz; backend'de (mission_executor) uygulanır.
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
}
