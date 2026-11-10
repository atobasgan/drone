import 'package:equatable/equatable.dart';
import 'package:drone_voice_control/domain/entities/drone_command.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';

/// Drone kontrol BLoC'u için state sınıfları
abstract class DroneState extends Equatable {
  const DroneState();

  @override
  List<Object?> get props => [];
}

/// Başlangıç durumu - bağlantı yok
class DroneInitial extends DroneState {
  const DroneInitial();
}

/// Drone'a bağlanılıyor
class DroneConnecting extends DroneState {
  const DroneConnecting();
}

/// Drone bağlı ve telemetri verisi mevcut
class DroneConnected extends DroneState {
  final DroneTelemetry telemetry;

  const DroneConnected({required this.telemetry});

  @override
  List<Object?> get props => [telemetry];
}

/// Komut başarıyla gönderildi
class DroneCommandSent extends DroneState {
  final DroneCommand command;
  final DroneTelemetry telemetry;

  const DroneCommandSent({
    required this.command,
    required this.telemetry,
  });

  @override
  List<Object?> get props => [command, telemetry];
}

/// Drone bağlantısı kesildi
class DroneDisconnected extends DroneState {
  const DroneDisconnected();
}

/// Drone bağlantı veya komut hatası
class DroneError extends DroneState {
  final String message;

  const DroneError({required this.message});

  @override
  List<Object?> get props => [message];
}
