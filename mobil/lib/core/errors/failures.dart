import 'package:equatable/equatable.dart';

/// Tüm hata tiplerinin temel sınıfı.
/// Clean Architecture'da domain katmanı hataları Failure olarak temsil edilir.
abstract class Failure extends Equatable {
  final String message;
  final int? code;

  const Failure({required this.message, this.code});

  @override
  List<Object?> get props => [message, code];
}

/// WebSocket / rosbridge bağlantı hatası
class ConnectionFailure extends Failure {
  const ConnectionFailure({
    super.message = 'Bağlantı kurulamadı',
    super.code,
  });
}

/// ROS topic yayınlama hatası
class PublishFailure extends Failure {
  const PublishFailure({
    super.message = 'Komut gönderilemedi',
    super.code,
  });
}

/// ROS topic abonelik hatası
class SubscriptionFailure extends Failure {
  const SubscriptionFailure({
    super.message = 'Topic dinlenemiyor',
    super.code,
  });
}

/// Ses tanıma hatası
class SpeechRecognitionFailure extends Failure {
  const SpeechRecognitionFailure({
    super.message = 'Ses tanıma başarısız',
    super.code,
  });
}

/// Mikrofon izin hatası
class PermissionFailure extends Failure {
  const PermissionFailure({
    super.message = 'Mikrofon izni verilmedi',
    super.code,
  });
}

/// Geçersiz komut hatası
class InvalidCommandFailure extends Failure {
  const InvalidCommandFailure({
    super.message = 'Geçersiz komut',
    super.code,
  });
}

/// Drone durum hatası (örn: yerdeyken iniş komutu)
class DroneStateFailure extends Failure {
  const DroneStateFailure({
    super.message = 'Drone bu durumda bu komutu kabul edemiyor',
    super.code,
  });
}

/// Zaman aşımı hatası
class TimeoutFailure extends Failure {
  const TimeoutFailure({
    super.message = 'İşlem zaman aşımına uğradı',
    super.code,
  });
}

/// Bilinmeyen / beklenmeyen hata
class UnknownFailure extends Failure {
  const UnknownFailure({
    super.message = 'Bilinmeyen bir hata oluştu',
    super.code,
  });
}
