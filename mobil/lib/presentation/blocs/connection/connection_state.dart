import 'package:equatable/equatable.dart';
import 'package:drone_voice_control/presentation/blocs/connection/connection_event.dart';

/// Bağlantı durumu BLoC'u için state sınıfları
abstract class ConnectionState extends Equatable {
  final ConnectionStatus status;

  const ConnectionState({required this.status});

  @override
  List<Object?> get props => [status];
}

/// Bağlantı başlangıç durumu
class ConnectionInitial extends ConnectionState {
  const ConnectionInitial() : super(status: ConnectionStatus.disconnected);
}

/// Bağlantı kuruluyor
class ConnectionInProgress extends ConnectionState {
  const ConnectionInProgress() : super(status: ConnectionStatus.connecting);
}

/// Bağlantı kuruldu
class ConnectionEstablished extends ConnectionState {
  final String host;
  final int port;

  const ConnectionEstablished({
    required this.host,
    required this.port,
  }) : super(status: ConnectionStatus.connected);

  @override
  List<Object?> get props => [status, host, port];
}

/// Bağlantı kesildi
class ConnectionLost extends ConnectionState {
  const ConnectionLost() : super(status: ConnectionStatus.disconnected);
}

/// Bağlantı hatası
class ConnectionFailed extends ConnectionState {
  final String message;

  const ConnectionFailed({required this.message})
      : super(status: ConnectionStatus.error);

  @override
  List<Object?> get props => [status, message];
}
