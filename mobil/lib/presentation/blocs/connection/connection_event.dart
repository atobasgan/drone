import 'package:equatable/equatable.dart';

/// Bağlantı durumu BLoC'u için event sınıfları
abstract class ConnectionEvent extends Equatable {
  const ConnectionEvent();

  @override
  List<Object?> get props => [];
}

/// Bağlantı durumunu kontrol et
class CheckConnection extends ConnectionEvent {
  const CheckConnection();
}

/// Bağlantı durumu değişti (dahili event)
class ConnectionChanged extends ConnectionEvent {
  final ConnectionStatus status;

  const ConnectionChanged({required this.status});

  @override
  List<Object?> get props => [status];
}

/// WebSocket bağlantı durumu enum'u
enum ConnectionStatus {
  /// Bağlantı yok
  disconnected,

  /// Bağlanılıyor
  connecting,

  /// Bağlı
  connected,

  /// Bağlantı hatası
  error,
}
