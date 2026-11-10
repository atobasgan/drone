import 'package:equatable/equatable.dart';
import 'package:drone_voice_control/domain/entities/drone_command.dart';

/// Ses tanıma BLoC'u için state sınıfları
abstract class VoiceState extends Equatable {
  const VoiceState();

  @override
  List<Object?> get props => [];
}

/// Başlangıç durumu - henüz dinleme yapılmadı
class VoiceInitial extends VoiceState {
  const VoiceInitial();
}

/// Aktif olarak dinleniyor (kullanıcı konuşurken ara metin tutabilir)
class VoiceListening extends VoiceState {
  final String? partialText;

  const VoiceListening({this.partialText});

  @override
  List<Object?> get props => [partialText];
}

/// Ses tanıma sonucu işleniyor
class VoiceProcessing extends VoiceState {
  final String rawText;

  const VoiceProcessing({required this.rawText});

  @override
  List<Object?> get props => [rawText];
}

/// Komut başarıyla tanındı
class VoiceCommandRecognized extends VoiceState {
  final DroneCommand command;
  final String rawText;
  final double confidence;

  const VoiceCommandRecognized({
    required this.command,
    required this.rawText,
    this.confidence = 1.0,
  });

  @override
  List<Object?> get props => [command, rawText, confidence];
}

/// Ses tanıma hatası
class VoiceError extends VoiceState {
  final String message;
  final String? lastSpokenText;

  const VoiceError({
    required this.message,
    this.lastSpokenText,
  });

  @override
  List<Object?> get props => [message, lastSpokenText];
}
