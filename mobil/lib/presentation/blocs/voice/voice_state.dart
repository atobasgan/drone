import 'package:equatable/equatable.dart';

/// Ses kaydı ve gönderim BLoC'u için state sınıfları
abstract class VoiceState extends Equatable {
  const VoiceState();

  @override
  List<Object?> get props => [];
}

/// Başlangıç durumu
class VoiceInitial extends VoiceState {
  const VoiceInitial();
}

/// Mikrofon kaydediyor (düğme basılı).
///
/// Ses telefonda yazıya çevrilmediği için konuşma sırasında metin yoktur;
/// [partialText] yalnızca görüntüleme uyumluluğu için tutulur ve boştur.
class VoiceListening extends VoiceState {
  final String? partialText;

  const VoiceListening({this.partialText});

  @override
  List<Object?> get props => [partialText];
}

/// Kayıt kapatılıyor / gönderiliyor. Hazır metin gönderiminde [rawText] doludur.
class VoiceProcessing extends VoiceState {
  final String? rawText;

  const VoiceProcessing({this.rawText});

  @override
  List<Object?> get props => [rawText];
}

/// Ses kaydı WAV olarak `/voice/audio` konusuna yayınlandı.
///
/// Konuşmanın metni backend STT'den `/voice/text` üzerinden gelir.
class VoiceAudioSent extends VoiceState {
  /// Kayıt süresi (ms)
  final int durationMs;

  /// Gönderim sırası: art arda aynı süreli kayıtlarda da durum değişsin diye
  final int sequence;

  const VoiceAudioSent({required this.durationMs, required this.sequence});

  @override
  List<Object?> get props => [durationMs, sequence];
}

/// Hazır metin `/voice/text` konusuna yayınlandı.
class VoiceTextSent extends VoiceState {
  final String rawText;

  /// Aynı metin art arda gönderildiğinde de durum değişsin diye gönderim sırası
  final int sequence;

  const VoiceTextSent({required this.rawText, required this.sequence});

  @override
  List<Object?> get props => [rawText, sequence];
}

/// Kayıt ya da gönderim hatası
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
