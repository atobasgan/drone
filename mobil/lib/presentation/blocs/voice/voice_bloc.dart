import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:drone_voice_control/data/datasources/voice_recorder.dart';
import 'package:drone_voice_control/domain/repositories/voice_uplink_repository.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_event.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_state.dart';

/// Bas-konuş kaydı ve gönderim BLoC'u.
///
/// Bir oturum şöyle akar:
///   StartListening → VoiceListening (mikrofon kaydediyor)
///   → StopListening → VoiceProcessing → VoiceAudioSent / VoiceError
///
/// Ses telefonda yazıya çevrilmez: kayıt WAV dosyası olarak `/voice/audio`
/// konusuna gönderilir; konuşma tanıma ve komut çözümü backend'dedir.
/// Hızlı komut düğmeleri (VoiceResultReceived) metni `/voice/text`'e yollar.
///
/// Tüm olaylar sırayla işlenir: bir kaydın kapanışı (son hece için kısa
/// bekleme dahil) bitmeden yeni kayıt başlamaz.
class VoiceBloc extends Bloc<VoiceEvent, VoiceState> {
  final VoiceRecorder voiceRecorder;
  final VoiceUplinkRepository voiceUplinkRepository;

  /// Bundan kısa kayıtlar gönderilmez (yanlış dokunuş)
  static const minDuration = Duration(milliseconds: 300);

  int _sentCount = 0;

  VoiceBloc({
    required this.voiceRecorder,
    required this.voiceUplinkRepository,
  }) : super(const VoiceInitial()) {
    on<VoiceEvent>(_onEvent, transformer: _sequential);
  }

  static Stream<E> _sequential<E>(Stream<E> events, EventMapper<E> mapper) =>
      events.asyncExpand(mapper);

  Future<void> _onEvent(VoiceEvent event, Emitter<VoiceState> emit) async {
    if (event is StartListening) {
      await _start(emit);
    } else if (event is StopListening) {
      await _stop(emit);
    } else if (event is VoiceResultReceived) {
      _sendText(event.text, emit);
    } else if (event is ResetVoice) {
      if (voiceRecorder.isRecording) await voiceRecorder.cancel();
      emit(const VoiceInitial());
    }
  }

  Future<void> _start(Emitter<VoiceState> emit) async {
    final ok = await voiceRecorder.start();
    if (ok) {
      emit(const VoiceListening());
    } else {
      emit(const VoiceError(
          message: 'Mikrofon açılamadı. Mikrofon iznini kontrol edin.'));
    }
  }

  Future<void> _stop(Emitter<VoiceState> emit) async {
    if (!voiceRecorder.isRecording) return;
    emit(const VoiceProcessing());

    final clip = await voiceRecorder.stop();
    if (clip.durationMs < minDuration.inMilliseconds) {
      emit(const VoiceError(
          message: 'Kayıt çok kısa. Düğmeye basılı tutup konuşun.'));
      return;
    }

    if (voiceUplinkRepository.sendAudioClip(clip)) {
      emit(VoiceAudioSent(durationMs: clip.durationMs, sequence: ++_sentCount));
    } else {
      emit(const VoiceError(
          message: 'Ses kaydı gönderilemedi: rosbridge bağlantısı yok.'));
    }
  }

  void _sendText(String text, Emitter<VoiceState> emit) {
    if (text.trim().isEmpty) return;
    emit(VoiceProcessing(rawText: text));
    if (voiceUplinkRepository.sendRawText(text)) {
      emit(VoiceTextSent(rawText: text, sequence: ++_sentCount));
    } else {
      emit(VoiceError(
        message: 'Metin gönderilemedi: rosbridge bağlantısı yok.',
        lastSpokenText: text,
      ));
    }
  }

  @override
  Future<void> close() async {
    if (voiceRecorder.isRecording) await voiceRecorder.cancel();
    return super.close();
  }
}
