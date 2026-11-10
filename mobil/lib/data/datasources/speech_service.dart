/// SpeechService - Ses tanıma servisi.
///
/// `speech_to_text` paketini sarmalayarak Türkçe (tr_TR) ses
/// tanıma desteği sağlar. Tanınan metni güvenilirlik skoru ile
/// birlikte stream olarak yayınlar.
library;

import 'dart:async';

import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Ses tanıma sonucunu temsil eden veri sınıfı.
class SpeechResult {
  /// Tanınan metin
  final String text;

  /// Güvenilirlik skoru (0.0 – 1.0)
  final double confidence;

  /// Tanıma işleminin tamamlanıp tamamlanmadığı
  final bool isFinal;

  const SpeechResult({
    required this.text,
    required this.confidence,
    required this.isFinal,
  });
}

/// Ses tanıma servisi.
///
/// `speech_to_text` paketini kullanarak cihazın mikrofonundan
/// ses dinler ve metne çevirir. Türkçe dil desteği sağlar.
class SpeechService {
  /// speech_to_text paketi instance'ı
  final SpeechToText _speech = SpeechToText();

  /// Tanıma sonuçlarını yayınlayan stream controller
  final _resultController = StreamController<SpeechResult>.broadcast();

  /// Tanıma hatalarını (Türkçe mesaj olarak) yayınlayan stream controller
  final _errorController = StreamController<String>.broadcast();

  /// Servisin başlatılıp başlatılmadığı
  bool _isInitialized = false;

  /// Tanıma sonuçlarının akışı
  Stream<SpeechResult> get resultStream => _resultController.stream;

  /// Tanıma hatalarının akışı (ör. "Ses anlaşılamadı")
  Stream<String> get errorStream => _errorController.stream;

  /// Dinlemenin aktif olup olmadığı.
  ///
  /// Kendi bayrağımızı tutmak yerine eklentinin durumunu okuruz: dinleme
  /// motor tarafından kendiliğinden bittiğinde bayrak bayat kalıp sonraki
  /// dinlemeyi engelliyordu.
  bool get isListening => _speech.isListening;

  /// Ses tanıma servisini başlatır.
  ///
  /// Mikrofon izni ister ve ses tanıma motorunu hazırlar.
  /// Başarılıysa `true` döndürür.
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      _isInitialized = await _speech.initialize(
        onStatus: _onStatus,
        onError: _onError,
        debugLogging: false,
      );

      if (_isInitialized) {
        _log('Ses tanıma servisi başlatıldı');
      } else {
        _log('Ses tanıma servisi başlatılamadı');
      }

      return _isInitialized;
    } catch (e) {
      _log('Başlatma hatası: $e');
      return false;
    }
  }

  /// Ses dinlemeyi başlatır.
  ///
  /// [locale] parametresi dil kodunu belirtir (varsayılan: "tr_TR").
  /// [listenFor] parametresi maksimum dinleme süresini belirtir.
  /// [pauseFor] parametresi sessizlik sonrası durma süresini belirtir.
  Future<bool> startListening({
    String locale = 'tr_TR',
    Duration listenFor = const Duration(seconds: 30),
    // Bas-konuşta bitişi buton belirler; kısa bir duraksamada kesilmesin.
    Duration pauseFor = const Duration(seconds: 10),
  }) async {
    if (!_isInitialized) {
      final success = await initialize();
      if (!success) return false;
    }

    // SpeechToText() bir singleton'dır ve Telsiz modülü (SistemTanima) ile
    // paylaşılır. initialize() yalnızca ilk çağrıda callback'leri kaydeder;
    // bu yüzden her dinlemeden önce kendi dinleyicilerimizi yeniden bağlarız.
    _speech.errorListener = _onError;
    _speech.statusListener = _onStatus;

    if (_speech.isListening) {
      // Önceki (yarım kalmış) oturumu kapat, yenisini temiz başlat.
      await _speech.cancel();
    }

    try {
      await _speech.listen(
        onResult: _onResult,
        listenOptions: SpeechListenOptions(
          localeId: locale,
          listenFor: listenFor,
          pauseFor: pauseFor,
          listenMode: ListenMode.dictation,
          cancelOnError: false,
          partialResults: true,
        ),
      );

      _log('Dinleme başladı (dil: $locale)');
      return true;
    } catch (e) {
      _log('Dinleme başlatma hatası: $e');
      return false;
    }
  }

  /// Ses dinlemeyi durdurur.
  Future<void> stopListening() async {
    try {
      await _speech.stop();
      _log('Dinleme durduruldu');
    } catch (e) {
      _log('Dinleme durdurma hatası: $e');
    }
  }

  /// Ses tanıma servisinin kullanılabilir olup olmadığını kontrol eder.
  Future<bool> get isAvailable async {
    if (!_isInitialized) {
      await initialize();
    }
    return _isInitialized;
  }

  /// Desteklenen dillerin listesini döndürür.
  Future<List<String>> getAvailableLocales() async {
    if (!_isInitialized) {
      await initialize();
    }

    final locales = await _speech.locales();
    return locales.map((l) => l.localeId).toList();
  }

  // ── Dahili Callback'ler ──

  /// Ses tanıma sonucu geldiğinde çağrılır.
  void _onResult(SpeechRecognitionResult result) {
    final speechResult = SpeechResult(
      text: result.recognizedWords,
      confidence: result.hasConfidenceRating ? result.confidence : 0.85,
      isFinal: result.finalResult,
    );

    if (!_resultController.isClosed) {
      _resultController.add(speechResult);
    }

    _log('Tanıma: "${result.recognizedWords}" '
        '(güven: ${speechResult.confidence}, '
        'final: ${result.finalResult})');
  }

  /// Ses tanıma durum değişikliğinde çağrılır.
  void _onStatus(String status) {
    _log('Durum: $status');
  }

  /// Ses tanıma hatası oluştuğunda çağrılır.
  void _onError(SpeechRecognitionError error) {
    _log('Hata: ${error.errorMsg} (kalıcı: ${error.permanent})');
    if (!_errorController.isClosed) {
      _errorController.add(_hataMesaji(error.errorMsg));
    }
  }

  /// Android/iOS hata kodlarını kullanıcıya gösterilecek Türkçe mesaja çevirir.
  String _hataMesaji(String kod) {
    switch (kod) {
      case 'error_no_match':
        return 'Ses anlaşılamadı, tekrar deneyin.';
      case 'error_speech_timeout':
        return 'Konuşma algılanmadı. Butona basılı tutup konuşun.';
      case 'error_network':
      case 'error_network_timeout':
      case 'error_server':
      case 'error_server_disconnected':
        return 'Ses tanıma için internet bağlantısı gerekli.';
      case 'error_language_not_supported':
      case 'error_language_unavailable':
        return 'Türkçe ses tanıma bu cihazda kullanılamıyor.';
      case 'error_permission':
      case 'error_insufficient_permissions':
        return 'Mikrofon izni verilmedi.';
      case 'error_busy':
      case 'error_recognizer_busy':
        return 'Ses tanıyıcı meşgul, biraz sonra tekrar deneyin.';
      case 'error_audio':
      case 'error_audio_error':
        return 'Mikrofondan ses alınamadı.';
      default:
        return 'Ses tanıma hatası: $kod';
    }
  }

  /// Debug log mesajı yazdırır.
  void _log(String message) {
    // ignore: avoid_print
    print('[SpeechService] $message');
  }

  /// Servisi kapatır ve kaynakları serbest bırakır.
  Future<void> dispose() async {
    await stopListening();
    await _resultController.close();
    await _errorController.close();
    _speech.cancel();
  }
}
