/// DroneRepository - Drone bağlantı ve kontrol işlemleri için soyut repository.
///
/// Domain katmanında tanımlanan bu arayüz, rosbridge WebSocket bağlantısının
/// nasıl yönetildiğine dair hiçbir detay içermez. Uygulama detayları
/// data katmanındaki `DroneRepositoryImpl` tarafından sağlanır.
library;

import '../entities/drone_telemetry.dart';

/// Drone bağlantı durumlarını tanımlayan enum.
enum DroneConnectionStatus {
  /// Bağlantı yok, bekleniyor
  disconnected,

  /// Bağlantı kuruluyor
  connecting,

  /// Bağlantı kuruldu, aktif
  connected,

  /// Bağlantı hatası oluştu
  error,

  /// Yeniden bağlanmaya çalışılıyor
  reconnecting,
}

/// Drone kontrol repository arayüzü.
///
/// Rosbridge WebSocket bağlantısını yönetmek ve telemetri verisi almak için
/// gerekli yöntemleri tanımlar. Komut metni [VoiceUplinkRepository] ile gönderilir.
abstract class DroneRepository {
  /// Rosbridge sunucusuna WebSocket bağlantısı kurar.
  ///
  /// [host] ve [port] parametreleri rosbridge adresini belirtir.
  /// Bağlantı başarılı olursa `true` döndürür.
  Future<bool> connect({required String host, required int port});

  /// Mevcut WebSocket bağlantısını kapatır.
  ///
  /// Abonelikleri iptal eder ve kaynakları temizler.
  Future<void> disconnect();

  /// Drone'dan gelen telemetri verilerinin akışı.
  ///
  /// `/drone/odometry` ve `/drone/imu` topic'lerinden
  /// gelen veriler birleştirilerek [DroneTelemetry] olarak yayınlanır.
  Stream<DroneTelemetry> get telemetryStream;

  /// Bağlantı durumunun akışı.
  ///
  /// Bağlantı durumu değiştiğinde yeni bir [DroneConnectionStatus] yayınlar.
  Stream<DroneConnectionStatus> get connectionStatus;

  /// Mevcut bağlantı durumunu döndürür.
  DroneConnectionStatus get currentConnectionStatus;

  /// WebSocket boolean bağlantı durumu akışı (true: bağlı, false: kesik).
  Stream<bool> get connectionStream;

  /// Drone'a / rosbridge'e bağlı mı?
  bool get isConnected;

  /// Mevcut bağlı olunan host adresi.
  String? get currentHost;

  /// Mevcut bağlı olunan port numarası.
  int? get currentPort;
}
