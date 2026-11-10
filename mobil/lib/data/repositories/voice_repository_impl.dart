import 'dart:async';
import 'package:drone_voice_control/data/datasources/speech_service.dart';
import 'package:drone_voice_control/domain/entities/voice_command.dart';
import 'package:drone_voice_control/domain/repositories/voice_repository.dart';

class VoiceRepositoryImpl implements VoiceRepository {
  final SpeechService speechService;
  final _commandStreamController = StreamController<VoiceCommand>.broadcast();
  StreamSubscription<SpeechResult>? _speechSubscription;
  StreamSubscription<String>? _errorSubscription;
  void Function(VoiceCommand)? _onResultCallback;
  void Function(String)? _onErrorCallback;

  VoiceRepositoryImpl({required this.speechService}) {
    _speechSubscription = speechService.resultStream.listen((result) {
      final voiceCommand = VoiceCommand(
        rawText: result.text,
        confidence: result.confidence,
        timestamp: DateTime.now(),
        isValid: result.text.trim().isNotEmpty,
        isFinal: result.isFinal,
      );
      _commandStreamController.add(voiceCommand);
      _onResultCallback?.call(voiceCommand);
    });
    // Dinleme sırasında motorun verdiği hatalar (anlaşılamadı, internet yok,
    // Türkçe yok...) daha önce yalnızca log'a yazılıyordu; artık BLoC'a iletilir.
    _errorSubscription = speechService.errorStream.listen((message) {
      _onErrorCallback?.call(message);
    });
  }

  Future<bool> initialize() async {
    return await speechService.initialize();
  }

  @override
  Future<bool> get isAvailable => speechService.isAvailable;

  @override
  bool get isListening => speechService.isListening;

  @override
  Stream<VoiceCommand> get voiceStream => _commandStreamController.stream;

  @override
  Future<bool> startListening({
    String locale = 'tr_TR',
    void Function(VoiceCommand)? onResult,
    void Function(String)? onError,
  }) async {
    _onResultCallback = onResult;
    _onErrorCallback = onError;

    try {
      final success = await speechService.startListening(locale: locale);
      if (!success) {
        _onErrorCallback?.call('Mikrofon dinleme başlatılamadı');
      }
      return success;
    } catch (e) {
      _onErrorCallback?.call(e.toString());
      return false;
    }
  }

  @override
  Future<void> stopListening() async {
    await speechService.stopListening();
  }

  void dispose() {
    _speechSubscription?.cancel();
    _errorSubscription?.cancel();
    _commandStreamController.close();
  }
}
