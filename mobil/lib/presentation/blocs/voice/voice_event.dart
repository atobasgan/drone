import 'package:equatable/equatable.dart';

/// Ses kaydı ve gönderim BLoC'u için event sınıfları
abstract class VoiceEvent extends Equatable {
  const VoiceEvent();

  @override
  List<Object?> get props => [];
}

/// Bas-konuş düğmesine basıldı: kayıt başlar
class StartListening extends VoiceEvent {
  const StartListening();
}

/// Düğme bırakıldı: kayıt biter ve WAV olarak gönderilir
class StopListening extends VoiceEvent {
  const StopListening();
}

/// Hazır metin (hızlı komut düğmesi) — sese gerek kalmadan `/voice/text`'e gider
class VoiceResultReceived extends VoiceEvent {
  final String text;

  const VoiceResultReceived({required this.text});

  @override
  List<Object?> get props => [text];
}

/// Durumu sıfırla (sürmekte olan kayıt atılır)
class ResetVoice extends VoiceEvent {
  const ResetVoice();
}
