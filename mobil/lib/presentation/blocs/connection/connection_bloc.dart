import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drone_voice_control/domain/repositories/drone_repository.dart';
import 'package:drone_voice_control/presentation/blocs/connection/connection_event.dart';
import 'package:drone_voice_control/presentation/blocs/connection/connection_state.dart'
    as conn;

/// WebSocket bağlantı durumunu izleyen BLoC
///
/// Rosbridge WebSocket bağlantısının durumunu takip eder
/// ve bağlantı değişikliklerini UI'a bildirir.
class ConnectionBloc extends Bloc<ConnectionEvent, conn.ConnectionState> {
  final DroneRepository droneRepository;

  StreamSubscription<bool>? _connectionSubscription;

  ConnectionBloc({
    required this.droneRepository,
  }) : super(const conn.ConnectionInitial()) {
    on<CheckConnection>(_onCheckConnection);
    on<ConnectionChanged>(_onConnectionChanged);

    // Bağlantı durumunu dinlemeye başla
    _connectionSubscription = droneRepository.connectionStream.listen(
      (isConnected) {
        add(ConnectionChanged(
          status: isConnected
              ? ConnectionStatus.connected
              : ConnectionStatus.disconnected,
        ));
      },
      onError: (_) {
        add(const ConnectionChanged(status: ConnectionStatus.error));
      },
    );
  }

  /// Bağlantı durumunu kontrol et
  Future<void> _onCheckConnection(
    CheckConnection event,
    Emitter<conn.ConnectionState> emit,
  ) async {
    try {
      final isConnected = droneRepository.isConnected;
      if (isConnected) {
        emit(conn.ConnectionEstablished(
          host: droneRepository.currentHost ?? '',
          port: droneRepository.currentPort ?? 0,
        ));
      } else {
        emit(const conn.ConnectionLost());
      }
    } catch (e) {
      emit(conn.ConnectionFailed(message: e.toString()));
    }
  }

  /// Bağlantı durumu değiştiğinde
  Future<void> _onConnectionChanged(
    ConnectionChanged event,
    Emitter<conn.ConnectionState> emit,
  ) async {
    switch (event.status) {
      case ConnectionStatus.connected:
        emit(conn.ConnectionEstablished(
          host: droneRepository.currentHost ?? '',
          port: droneRepository.currentPort ?? 0,
        ));
        break;
      case ConnectionStatus.connecting:
        emit(const conn.ConnectionInProgress());
        break;
      case ConnectionStatus.disconnected:
        emit(const conn.ConnectionLost());
        break;
      case ConnectionStatus.error:
        emit(const conn.ConnectionFailed(message: 'Bağlantı hatası'));
        break;
    }
  }

  @override
  Future<void> close() {
    _connectionSubscription?.cancel();
    return super.close();
  }
}
