import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drone_voice_control/domain/repositories/voice_repository.dart';
import 'package:drone_voice_control/domain/usecases/process_voice_command.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_event.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_state.dart';

/// Ses tanıma ve komut işleme BLoC'u
///
/// Bir bas-konuş oturumu şöyle akar:
///   StartListening → (ara sonuçlar: VoiceListening(partialText))
///   → buton bırakılır (StopListening) → motorun son sonucu beklenir
///   → tek bir kez VoiceProcessing → VoiceCommandRecognized / VoiceError
///
/// Oturum bir kez sonuçlandıktan sonra gelen geç/çift sonuçlar yok sayılır;
/// böylece aynı komut drone'a iki kez gönderilmez ve ekran "dinleniyor"a geri
/// dönmez.
class VoiceBloc extends Bloc<VoiceEvent, VoiceState> {
  final VoiceRepository voiceRepository;
  final ProcessVoiceCommand processVoiceCommand;

  /// Buton bırakıldıktan sonra motorun son sonucunu bekleme süresi
  static const _finalResultTimeout = Duration(milliseconds: 1500);

  /// Mikrofon oturumu açık ve henüz sonuçlanmadı mı?
  bool _sessionActive = false;

  /// Bu oturumda duyulan en son ara metin
  String? _lastPartial;

  /// Oturum sonuçlandığında (final sonuç ya da hata) tamamlanır
  Completer<void>? _sessionDone;

  /// Her StartListening'de artar; bekleyen eski bir StopListening'in yeni
  /// oturumu kapatmasını engeller.
  int _sessionId = 0;

  VoiceBloc({
    required this.voiceRepository,
    required this.processVoiceCommand,
  }) : super(const VoiceInitial()) {
    on<StartListening>(_onStartListening);
    on<StopListening>(_onStopListening);
    on<VoiceResultReceived>(_onVoiceResultReceived);
    on<VoiceRecognitionFailed>(_onVoiceRecognitionFailed);
    on<ResetVoice>(_onResetVoice);
  }

  /// Oturumu kapatır. Zaten kapalıysa `false` döner (sonuç önceden işlendi).
  bool _closeSession() {
    if (!_sessionActive) return false;
    _sessionActive = false;
    final done = _sessionDone;
    if (done != null && !done.isCompleted) done.complete();
    return true;
  }

  /// Ses dinlemeyi başlat (Mikrofon açılır)
  Future<void> _onStartListening(
    StartListening event,
    Emitter<VoiceState> emit,
  ) async {
    _sessionId++;
    _sessionActive = true;
    _lastPartial = null;
    _sessionDone = Completer<void>();
    emit(const VoiceListening());

    try {
      await voiceRepository.startListening(
        onResult: (voiceCommand) {
          // Callback'ler handler bittikten sonra da gelir: emit yerine add.
          add(VoiceResultReceived(
            text: voiceCommand.rawText,
            confidence: voiceCommand.confidence,
            isFinal: voiceCommand.isFinal,
            fromMic: true,
          ));
        },
        onError: (errorMessage) {
          add(VoiceRecognitionFailed(message: errorMessage));
        },
      );
    } catch (e) {
      add(VoiceRecognitionFailed(message: 'Mikrofon başlatılamadı: $e'));
    }
  }

  /// Ses dinlemeyi durdur (buton bırakıldı)
  Future<void> _onStopListening(
    StopListening event,
    Emitter<VoiceState> emit,
  ) async {
    final sessionId = _sessionId;
    try {
      await voiceRepository.stopListening();
    } catch (_) {}

    // stop() sonrası motor kesinleşmiş metni biraz gecikmeli gönderir; bekle.
    final done = _sessionDone;
    if (_sessionActive && done != null && !done.isCompleted) {
      await done.future.timeout(_finalResultTimeout, onTimeout: () {});
    }

    // Bu arada yeni bir oturum başladıysa ona dokunma.
    if (sessionId != _sessionId) return;

    // Final sonuç ya da hata geldiyse oturum zaten işlendi.
    if (!_closeSession()) return;

    // Final sonuç gelmedi: son ara metni komut olarak işle.
    final partial = _lastPartial;
    if (partial != null && partial.trim().isNotEmpty) {
      await _processText(partial, 1.0, emit);
    } else {
      emit(const VoiceError(
        message: 'Ses algılanamadı. Butona basılı tutup konuşun.',
      ));
    }
  }

  /// Ses tanıma sonucu alındığında
  Future<void> _onVoiceResultReceived(
    VoiceResultReceived event,
    Emitter<VoiceState> emit,
  ) async {
    if (event.fromMic) {
      // Oturum kapandıktan sonra gelen geç/çift sonuçları yok say.
      if (!_sessionActive) return;

      // Ara sonuç: kullanıcı hâlâ konuşuyor, ekranı anlık güncelle.
      if (!event.isFinal) {
        if (event.text.trim().isNotEmpty) _lastPartial = event.text;
        emit(VoiceListening(partialText: _lastPartial));
        return;
      }

      _closeSession();

      // Motor bazen boş final gönderir; elimizdeki ara metni kullan.
      final text = event.text.trim().isNotEmpty ? event.text : (_lastPartial ?? '');
      if (text.trim().isEmpty) {
        emit(const VoiceError(
          message: 'Ses algılanamadı. Butona basılı tutup konuşun.',
        ));
        return;
      }
      await _processText(text, event.confidence, emit);
      return;
    }

    // Hızlı komut butonları
    await _processText(event.text, event.confidence, emit);
  }

  /// Ses tanıma motoru hata verdiğinde
  Future<void> _onVoiceRecognitionFailed(
    VoiceRecognitionFailed event,
    Emitter<VoiceState> emit,
  ) async {
    if (!_closeSession()) return;

    try {
      await voiceRepository.stopListening();
    } catch (_) {}

    // Hata gelmeden önce bir şey duyulduysa onu kaybetme.
    final partial = _lastPartial;
    if (partial != null && partial.trim().isNotEmpty) {
      await _processText(partial, 1.0, emit);
    } else {
      emit(VoiceError(message: event.message));
    }
  }

  /// Metni drone komutuna çevirir ve sonucu yayınlar.
  Future<void> _processText(
    String text,
    double confidence,
    Emitter<VoiceState> emit,
  ) async {
    emit(VoiceProcessing(rawText: text));

    try {
      final voiceCommand = await processVoiceCommand(
        rawText: text,
        confidence: confidence,
      );

      if (voiceCommand.isValid && voiceCommand.parsedCommand != null) {
        emit(VoiceCommandRecognized(
          command: voiceCommand.parsedCommand!,
          rawText: text,
          confidence: confidence,
        ));
      } else {
        emit(VoiceError(
          message: 'Anlaşılamayan komut: "$text". (Örn: "ileri", "yüksel", "dur")',
          lastSpokenText: text,
        ));
      }
    } catch (e) {
      emit(VoiceError(
        message: 'Ses komutu işlenirken hata: ${e.toString()}',
        lastSpokenText: text,
      ));
    }
  }

  /// Ses durumunu sıfırla
  Future<void> _onResetVoice(
    ResetVoice event,
    Emitter<VoiceState> emit,
  ) async {
    _closeSession();
    emit(const VoiceInitial());
  }

  @override
  Future<void> close() {
    _closeSession();
    return super.close();
  }
}
