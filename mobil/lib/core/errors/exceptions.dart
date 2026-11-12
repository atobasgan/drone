/// Tüm özel exception tiplerinin temel sınıfı.
/// Data katmanında fırlatılır, repository'de Failure'a dönüştürülür.
class AppException implements Exception {
  final String message;
  final int? code;
  final dynamic originalError;

  const AppException({
    required this.message,
    this.code,
    this.originalError,
  });

  @override
  String toString() => 'AppException: $message (code: $code)';
}

/// WebSocket bağlantı exception'ı
class ConnectionException extends AppException {
  const ConnectionException({
    super.message = 'WebSocket bağlantısı kurulamadı',
    super.code,
    super.originalError,
  });
}

/// WebSocket bağlantı kopması
class DisconnectionException extends AppException {
  const DisconnectionException({
    super.message = 'WebSocket bağlantısı kesildi',
    super.code,
    super.originalError,
  });
}

/// ROS mesaj yayınlama exception'ı
class PublishException extends AppException {
  const PublishException({
    super.message = 'ROS mesajı yayınlanamadı',
    super.code,
    super.originalError,
  });
}

/// ROS topic abonelik exception'ı
class SubscriptionException extends AppException {
  const SubscriptionException({
    super.message = 'ROS topic aboneliği başarısız',
    super.code,
    super.originalError,
  });
}

/// Ses tanıma exception'ı
class SpeechRecognitionException extends AppException {
  const SpeechRecognitionException({
    super.message = 'Ses tanıma işlemi başarısız',
    super.code,
    super.originalError,
  });
}

/// İzin reddedildi exception'ı
class PermissionDeniedException extends AppException {
  const PermissionDeniedException({
    super.message = 'Gerekli izin verilmedi',
    super.code,
    super.originalError,
  });
}

/// Geçersiz komut exception'ı
class InvalidCommandException extends AppException {
  const InvalidCommandException({
    super.message = 'Tanınmayan veya geçersiz komut',
    super.code,
    super.originalError,
  });
}

/// Zaman aşımı exception'ı
class TimeoutException extends AppException {
  const TimeoutException({
    super.message = 'İşlem zaman aşımına uğradı',
    super.code,
    super.originalError,
  });
}

/// Serileştirme / deserileştirme exception'ı
class SerializationException extends AppException {
  const SerializationException({
    super.message = 'Veri dönüştürme hatası',
    super.code,
    super.originalError,
  });
}
