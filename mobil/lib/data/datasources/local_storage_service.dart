/// LocalStorageService - Yerel depolama servisi.
///
/// `shared_preferences` paketini sarmalayarak uygulama ayarlarının
/// kalıcı olarak saklanmasını sağlar.
library;

import 'package:shared_preferences/shared_preferences.dart';

/// SharedPreferences sarmalayıcı servisi.
///
/// Uygulama ayarlarını (rosbridge adresi, port, dil, hız limitleri vb.)
/// cihazın yerel depolama alanında saklar.
class LocalStorageService {
  /// SharedPreferences instance'ı
  SharedPreferences? _prefs;

  // ── Anahtar sabitleri ──

  /// Rosbridge sunucu adresi anahtarı
  static const String keyRosbridgeHost = 'rosbridge_host';

  /// Rosbridge port numarası anahtarı
  static const String keyRosbridgePort = 'rosbridge_port';

  /// Dil tercihi anahtarı
  static const String keyLanguage = 'language';

  /// Maksimum hız anahtarı
  static const String keyMaxSpeed = 'max_speed';

  /// Güvenlik limitleri — maksimum lineer XY hızı
  static const String keyMaxLinearXY = 'safety_max_linear_xy';

  /// Güvenlik limitleri — maksimum lineer Z hızı
  static const String keyMaxLinearZ = 'safety_max_linear_z';

  /// Güvenlik limitleri — maksimum açısal Z hızı
  static const String keyMaxAngularZ = 'safety_max_angular_z';

  /// Güvenlik limitleri — hız adımı
  static const String keySpeedStep = 'safety_speed_step';

  // ── Varsayılan değerler ──

  /// Varsayılan rosbridge sunucu adresi
  static const String defaultHost = '192.168.1.100';

  /// Varsayılan rosbridge port numarası
  static const int defaultPort = 9090;

  /// Varsayılan dil
  static const String defaultLanguage = 'tr_TR';

  /// Varsayılan maksimum hız (m/s)
  static const double defaultMaxSpeed = 3.0;

  /// Servisi başlatır ve SharedPreferences instance'ını alır.
  Future<void> initialize() async {
    _prefs ??= await SharedPreferences.getInstance();
  }

  /// SharedPreferences'ın hazır olduğundan emin olur.
  Future<SharedPreferences> _ensureInitialized() async {
    if (_prefs == null) {
      await initialize();
    }
    return _prefs!;
  }

  // ── String İşlemleri ──

  /// String değer okur. Bulunamazsa [defaultValue] döndürür.
  Future<String> getString(String key, {String defaultValue = ''}) async {
    final prefs = await _ensureInitialized();
    return prefs.getString(key) ?? defaultValue;
  }

  /// String değer kaydeder.
  Future<void> setString(String key, String value) async {
    final prefs = await _ensureInitialized();
    await prefs.setString(key, value);
  }

  // ── Int İşlemleri ──

  /// Int değer okur. Bulunamazsa [defaultValue] döndürür.
  Future<int> getInt(String key, {int defaultValue = 0}) async {
    final prefs = await _ensureInitialized();
    return prefs.getInt(key) ?? defaultValue;
  }

  /// Int değer kaydeder.
  Future<void> setInt(String key, int value) async {
    final prefs = await _ensureInitialized();
    await prefs.setInt(key, value);
  }

  // ── Double İşlemleri ──

  /// Double değer okur. Bulunamazsa [defaultValue] döndürür.
  Future<double> getDouble(String key, {double defaultValue = 0.0}) async {
    final prefs = await _ensureInitialized();
    return prefs.getDouble(key) ?? defaultValue;
  }

  /// Double değer kaydeder.
  Future<void> setDouble(String key, double value) async {
    final prefs = await _ensureInitialized();
    await prefs.setDouble(key, value);
  }

  // ── Bool İşlemleri ──

  /// Bool değer okur. Bulunamazsa [defaultValue] döndürür.
  Future<bool> getBool(String key, {bool defaultValue = false}) async {
    final prefs = await _ensureInitialized();
    return prefs.getBool(key) ?? defaultValue;
  }

  /// Bool değer kaydeder.
  Future<void> setBool(String key, bool value) async {
    final prefs = await _ensureInitialized();
    await prefs.setBool(key, value);
  }

  // ── Yardımcı Yöntemler ──

  /// Belirtilen anahtarı siler.
  Future<void> remove(String key) async {
    final prefs = await _ensureInitialized();
    await prefs.remove(key);
  }

  /// Tüm ayarları temizler.
  Future<void> clear() async {
    final prefs = await _ensureInitialized();
    await prefs.clear();
  }

  /// Belirtilen anahtarın var olup olmadığını kontrol eder.
  Future<bool> containsKey(String key) async {
    final prefs = await _ensureInitialized();
    return prefs.containsKey(key);
  }
}
