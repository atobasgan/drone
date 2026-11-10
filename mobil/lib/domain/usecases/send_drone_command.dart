/// SendDroneCommand - Drone'a komut gönderme use case'i.
///
/// Güvenlik limitlerini kontrol ettikten sonra komutu
/// drone repository üzerinden gönderir.
library;

import '../entities/drone_command.dart';
import '../repositories/drone_repository.dart';
import '../repositories/settings_repository.dart';

/// Drone'a komut gönderme sonucunu temsil eden sınıf.
class SendCommandResult {
  /// Komutun başarıyla gönderilip gönderilmediği
  final bool success;

  /// Hata veya bilgi mesajı
  final String? message;

  /// Gönderilen (veya sınırlandırılmış) komut
  final DroneCommand command;

  const SendCommandResult({
    required this.success,
    this.message,
    required this.command,
  });
}

/// Drone'a komut gönderen use case sınıfı.
///
/// Komut gönderilmeden önce:
/// 1. Bağlantı durumu kontrol edilir
/// 2. Güvenlik limitleri uygulanır (hız değerleri sınırlandırılır)
/// 3. Komut rosbridge üzerinden `/drone/cmd_vel` topic'ine yayınlanır
class SendDroneCommand {
  /// Drone ile iletişim için repository
  final DroneRepository _droneRepository;

  /// Güvenlik limitlerine erişim için ayarlar repository'si
  final SettingsRepository _settingsRepository;

  SendDroneCommand(this._droneRepository, this._settingsRepository);

  /// Komutu güvenlik kontrollerinden geçirip drone'a gönderir.
  ///
  /// [command] parametresi gönderilecek hareket komutudur.
  /// Döndürülen [SendCommandResult] sonucun başarılı olup olmadığını,
  /// varsa hata mesajını ve son halini içerir.
  Future<SendCommandResult> call(DroneCommand command) async {
    // ── 1. Bağlantı durumu kontrolü ──
    final connectionStatus = _droneRepository.currentConnectionStatus;
    if (connectionStatus != DroneConnectionStatus.connected) {
      return SendCommandResult(
        success: false,
        message: 'Drone bağlantısı yok. Durum: $connectionStatus',
        command: command,
      );
    }

    // ── 2. Güvenlik limitleri uygula ──
    final limits = await _settingsRepository.getSafetyLimits();
    final safeCommand = _applySafetyLimits(command, limits);

    // ── 3. Komutu gönder ──
    try {
      final success = await _droneRepository.sendCommand(safeCommand);

      if (success) {
        return SendCommandResult(
          success: true,
          message: 'Komut başarıyla gönderildi',
          command: safeCommand,
        );
      } else {
        return SendCommandResult(
          success: false,
          message: 'Komut gönderilemedi',
          command: safeCommand,
        );
      }
    } catch (e) {
      return SendCommandResult(
        success: false,
        message: 'Komut gönderilirken hata oluştu: $e',
        command: safeCommand,
      );
    }
  }

  /// Güvenlik limitlerini komutu uygular.
  ///
  /// Hız değerlerini belirlenen maksimum değerlerin içine sınırlar.
  DroneCommand _applySafetyLimits(DroneCommand command, SafetyLimits limits) {
    return DroneCommand(
      commandType: command.commandType,
      linearX: _clamp(command.linearX, -limits.maxLinearXY, limits.maxLinearXY),
      linearY: _clamp(command.linearY, -limits.maxLinearXY, limits.maxLinearXY),
      linearZ: _clamp(command.linearZ, -limits.maxLinearZ, limits.maxLinearZ),
      angularZ: _clamp(command.angularZ, -limits.maxAngularZ, limits.maxAngularZ),
      timestamp: command.timestamp,
    );
  }

  /// Bir değeri minimum ve maksimum arasında sınırlar.
  double _clamp(double value, double min, double max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
  }
}
