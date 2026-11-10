import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drone_voice_control/domain/entities/drone_command.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';
import 'package:drone_voice_control/domain/repositories/drone_repository.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_event.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_state.dart';

/// Drone kontrol ve telemetri BLoC'u
///
/// Gazebo Sim drone'una rosbridge WebSocket üzerinden bağlanır,
/// /drone/cmd_vel konusuna Twist komutları gönderir ve
/// /drone/odometry ile /drone/imu verilerini dinler.
class DroneBloc extends Bloc<DroneEvent, DroneState> {
  final DroneRepository droneRepository;

  StreamSubscription<DroneTelemetry>? _telemetrySubscription;
  StreamSubscription<DroneConnectionStatus>? _statusSubscription;

  DroneBloc({
    required this.droneRepository,
  }) : super(const DroneInitial()) {
    on<ConnectDrone>(_onConnectDrone);
    on<DisconnectDrone>(_onDisconnectDrone);
    on<SendCommand>(_onSendCommand);
    on<EmergencyStop>(_onEmergencyStop);
    on<TelemetryUpdated>(_onTelemetryUpdated);

    // Bağlantı durumunu dinle
    _statusSubscription = droneRepository.connectionStatus.listen((status) {
      if (status == DroneConnectionStatus.disconnected) {
        add(const DisconnectDrone());
      }
    });
  }

  /// Drone'a bağlan
  Future<void> _onConnectDrone(
    ConnectDrone event,
    Emitter<DroneState> emit,
  ) async {
    emit(const DroneConnecting());

    try {
      final success = await droneRepository.connect(
        host: event.host,
        port: event.port,
      );

      if (success) {
        _telemetrySubscription?.cancel();
        _telemetrySubscription = droneRepository.telemetryStream.listen(
          (telemetry) => add(TelemetryUpdated(telemetry: telemetry)),
          onError: (error) {
            add(const DisconnectDrone());
          },
        );

        emit(DroneConnected(telemetry: DroneTelemetry.initial()));
      } else {
        emit(const DroneError(message: 'Drone bağlantısı kurulamadı. rosbridge_websocket çalışıyor mu?'));
      }
    } catch (e) {
      emit(DroneError(message: 'Bağlantı hatası: ${e.toString()}'));
    }
  }

  /// Drone bağlantısını kes
  Future<void> _onDisconnectDrone(
    DisconnectDrone event,
    Emitter<DroneState> emit,
  ) async {
    await _telemetrySubscription?.cancel();
    _telemetrySubscription = null;

    try {
      await droneRepository.disconnect();
    } catch (_) {}

    emit(const DroneDisconnected());
  }

  /// Drone'a komut gönder
  Future<void> _onSendCommand(
    SendCommand event,
    Emitter<DroneState> emit,
  ) async {
    try {
      await droneRepository.sendCommand(event.command);

      final currentTelemetry = _getCurrentTelemetry();
      emit(DroneCommandSent(
        command: event.command,
        telemetry: currentTelemetry,
      ));
    } catch (e) {
      emit(DroneError(message: 'Komut gönderilemedi: ${e.toString()}'));
    }
  }

  /// Acil durum durdurma - tüm hızları sıfırla (hover/stop)
  Future<void> _onEmergencyStop(
    EmergencyStop event,
    Emitter<DroneState> emit,
  ) async {
    try {
      final stopCmd = DroneCommand.hover();
      await droneRepository.sendCommand(stopCmd);

      final currentTelemetry = _getCurrentTelemetry();
      emit(DroneCommandSent(
        command: stopCmd,
        telemetry: currentTelemetry,
      ));
    } catch (e) {
      emit(DroneError(message: 'Acil durdurma başarısız: ${e.toString()}'));
    }
  }

  /// Telemetri verisi güncellendi
  Future<void> _onTelemetryUpdated(
    TelemetryUpdated event,
    Emitter<DroneState> emit,
  ) async {
    emit(DroneConnected(telemetry: event.telemetry));
  }

  DroneTelemetry _getCurrentTelemetry() {
    if (state is DroneConnected) {
      return (state as DroneConnected).telemetry;
    } else if (state is DroneCommandSent) {
      return (state as DroneCommandSent).telemetry;
    }
    return DroneTelemetry.initial();
  }

  @override
  Future<void> close() {
    _telemetrySubscription?.cancel();
    _statusSubscription?.cancel();
    return super.close();
  }
}
