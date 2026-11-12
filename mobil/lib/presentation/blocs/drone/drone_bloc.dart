import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';
import 'package:drone_voice_control/domain/repositories/drone_repository.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_event.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_state.dart';

/// Drone kontrol ve telemetri BLoC'u
///
/// Rosbridge WebSocket bağlantısını yönetir ve /drone/odometry ile
/// /drone/imu verilerini dinler. Komut üretmez ve göndermez.
class DroneBloc extends Bloc<DroneEvent, DroneState> {
  final DroneRepository droneRepository;

  StreamSubscription<DroneTelemetry>? _telemetrySubscription;
  StreamSubscription<DroneConnectionStatus>? _statusSubscription;

  DroneBloc({
    required this.droneRepository,
  }) : super(const DroneInitial()) {
    on<ConnectDrone>(_onConnectDrone);
    on<DisconnectDrone>(_onDisconnectDrone);
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

  /// Telemetri verisi güncellendi
  Future<void> _onTelemetryUpdated(
    TelemetryUpdated event,
    Emitter<DroneState> emit,
  ) async {
    emit(DroneConnected(telemetry: event.telemetry));
  }

  @override
  Future<void> close() {
    _telemetrySubscription?.cancel();
    _statusSubscription?.cancel();
    return super.close();
  }
}
