import 'package:equatable/equatable.dart';
import 'package:drone_voice_control/domain/entities/drone_command.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';

/// Drone kontrol BLoC'u için event sınıfları
abstract class DroneEvent extends Equatable {
  const DroneEvent();

  @override
  List<Object?> get props => [];
}

/// Drone'a bağlan
class ConnectDrone extends DroneEvent {
  final String host;
  final int port;

  const ConnectDrone({
    required this.host,
    required this.port,
  });

  @override
  List<Object?> get props => [host, port];
}

/// Drone bağlantısını kes
class DisconnectDrone extends DroneEvent {
  const DisconnectDrone();
}

/// Drone'a komut gönder
class SendCommand extends DroneEvent {
  final DroneCommand command;

  const SendCommand({required this.command});

  @override
  List<Object?> get props => [command];
}

/// Acil durum durdurma
class EmergencyStop extends DroneEvent {
  const EmergencyStop();
}

/// Telemetri verisi güncellendi (dahili event)
class TelemetryUpdated extends DroneEvent {
  final DroneTelemetry telemetry;

  const TelemetryUpdated({required this.telemetry});

  @override
  List<Object?> get props => [telemetry];
}
