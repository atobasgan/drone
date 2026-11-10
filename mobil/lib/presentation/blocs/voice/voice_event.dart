import 'package:equatable/equatable.dart';

/// Ses tanıma BLoC'u için event sınıfları
abstract class VoiceEvent extends Equatable {
  const VoiceEvent();

  @override
  List<Object?> get props => [];
}

/// Ses dinlemeyi başlat
class StartListening extends VoiceEvent {
  const StartListening();
}

/// Ses dinlemeyi durdur
class StopListening extends VoiceEvent {
  const StopListening();
}

/// Ses tanıma sonucu alındı
class VoiceResultReceived extends VoiceEvent {
  final String text;
  final double confidence;
  final bool isFinal;

  /// Sonuç mikrofondaki tanıma oturumundan mı geldi? (Hızlı komut
  /// butonlarından gelenler `false`'tur ve oturum durumuna bakılmaz.)
  final bool fromMic;

  const VoiceResultReceived({
    required this.text,
    this.confidence = 1.0,
    this.isFinal = true,
    this.fromMic = false,
  });

  @override
  List<Object?> get props => [text, confidence, isFinal, fromMic];
}

/// Ses tanıma motoru dinleme sırasında hata verdi
class VoiceRecognitionFailed extends VoiceEvent {
  final String message;

  const VoiceRecognitionFailed({required this.message});

  @override
  List<Object?> get props => [message];
}

/// Ses durumunu sıfırla
class ResetVoice extends VoiceEvent {
  const ResetVoice();
}
