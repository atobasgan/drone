/// GetDroneTelemetry - Drone telemetri akışını sağlayan use case.
///
/// Drone repository'den gelen telemetri stream'ini döndürür.
/// `/drone/odometry` ve `/drone/imu` topic'lerinden alınan veriler
/// birleştirilerek kullanıcıya sunulur.
library;

import '../entities/drone_telemetry.dart';
import '../repositories/drone_repository.dart';

/// Drone telemetri verilerini sağlayan use case sınıfı.
///
/// Basit bir stream proxy'dir — telemetri verisini drone repository'den alır
/// ve sunum katmanına iletir.
class GetDroneTelemetry {
  /// Telemetri verisine erişim için drone repository
  final DroneRepository _droneRepository;

  GetDroneTelemetry(this._droneRepository);

  /// Drone telemetri verilerinin akışını döndürür.
  ///
  /// Bu stream sürekli aktiftir ve drone bağlı olduğu sürece
  /// güncellenen [DroneTelemetry] nesneleri yayınlar.
  Stream<DroneTelemetry> call() {
    return _droneRepository.telemetryStream;
  }

  /// Bağlantı durumu akışını döndürür.
  ///
  /// Telemetri alabilmek için önce bağlantının kurulmuş olması gerekir.
  Stream<DroneConnectionStatus> get connectionStatus {
    return _droneRepository.connectionStatus;
  }
}
