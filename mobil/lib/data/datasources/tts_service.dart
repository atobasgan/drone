/// TtsService - Metin-konuşma (Text-to-Speech) servisi.
///
/// Drone komut onaylarını Türkçe sesli olarak kullanıcıya bildirir.
/// `flutter_tts` paketini sarmalayarak TTS işlemlerini yönetir.
library;

import 'dart:async';

import 'package:flutter_tts/flutter_tts.dart';

/// Metin-konuşma servisi.
///
/// Komut onayları, hata bildirimleri ve durum güncellemelerini
/// Türkçe sesli olarak kullanıcıya iletir.
class TtsService {
  /// flutter_tts paketi instance'ı
  final FlutterTts _flutterTts = FlutterTts();

  /// TTS'in konuşup konuşmadığını takip eden bayrak
  bool _isSpeaking = false;

  /// Servisin başlatılıp başlatılmadığı
  bool _isInitialized = false;

  /// TTS'in konuşup konuşmadığı
  bool get isSpeaking => _isSpeaking;

  /// TTS servisini Türkçe ayarlarıyla başlatır.
  ///
  /// Dil, hız, ton ve ses yüksekliği yapılandırılır.
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // Türkçe ses motorda var mı? Yoksa konuşma sessizce başarısız olur.
      final turkceVar = await _flutterTts.isLanguageAvailable('tr-TR');
      if (turkceVar != true) {
        _log('UYARI: Cihazda Türkçe TTS sesi yok/indirilmemiş. '
            'Ayarlar > Metin okuma çıkışı > Türkçe ses verisini yükleyin.');
      }

      // Türkçe dilini ayarla
      await _flutterTts.setLanguage('tr-TR');

      // speak() okuma bitene kadar beklemesin; yeni onay eskisini keser.
      await _flutterTts.awaitSpeakCompletion(false);

      // Konuşma hızını ayarla (0.0 – 1.0, varsayılan: 0.5)
      await _flutterTts.setSpeechRate(0.5);

      // Ses tonunu ayarla (0.5 – 2.0, varsayılan: 1.0)
      await _flutterTts.setPitch(1.0);

      // Ses yüksekliğini ayarla (0.0 – 1.0)
      await _flutterTts.setVolume(1.0);

      // Callback'leri ayarla
      _flutterTts.setStartHandler(() {
        _isSpeaking = true;
      });

      _flutterTts.setCompletionHandler(() {
        _isSpeaking = false;
      });

      _flutterTts.setErrorHandler((message) {
        _isSpeaking = false;
        _log('TTS hatası: $message');
      });

      _flutterTts.setCancelHandler(() {
        _isSpeaking = false;
      });

      _isInitialized = true;
      _log('TTS servisi başlatıldı (Türkçe)');
    } catch (e) {
      _log('TTS başlatma hatası: $e');
    }
  }

  /// Verilen metni Türkçe olarak seslendirir.
  ///
  /// [text]: Seslendirilecek metin
  /// Eğer halihazırda konuşma varsa önce durdurulur.
  Future<void> speak(String text) async {
    if (!_isInitialized) await initialize();

    // Mevcut konuşmayı durdur (bayrak bazen geç güncellenir; her zaman durdur)
    await stop();

    try {
      // focus: true → Android'de ses odağı (audio focus) istenir. Mikrofon /
      // konuşma tanıyıcı sesi bırakırken onay kısılmasın ya da kaybolmasın.
      final sonuc = await _flutterTts.speak(text, focus: true);
      if (sonuc != 1) _log('Konuşma başlatılamadı (sonuç: $sonuc)');
      _log('Konuşuluyor: "$text"');
    } catch (e) {
      _log('Konuşma hatası: $e');
    }
  }

  /// Mevcut konuşmayı durdurur.
  Future<void> stop() async {
    try {
      await _flutterTts.stop();
      _isSpeaking = false;
    } catch (e) {
      _log('Durdurma hatası: $e');
    }
  }

  // ── Komut onay mesajları ──

  /// İleri hareket onayı
  Future<void> confirmForward() => speak('İleri gidiyorum');

  /// Geri hareket onayı
  Future<void> confirmBackward() => speak('Geri gidiyorum');

  /// Sola hareket onayı
  Future<void> confirmLeft() => speak('Sola gidiyorum');

  /// Sağa hareket onayı
  Future<void> confirmRight() => speak('Sağa gidiyorum');

  /// Yukarı hareket onayı
  Future<void> confirmUp() => speak('Yükseliyorum');

  /// Aşağı hareket onayı
  Future<void> confirmDown() => speak('Alçalıyorum');

  /// Sola dönüş onayı
  Future<void> confirmRotateLeft() => speak('Sola dönüyorum');

  /// Sağa dönüş onayı
  Future<void> confirmRotateRight() => speak('Sağa dönüyorum');

  /// Durma onayı
  Future<void> confirmHover() => speak('Duruyorum');

  /// Bağlantı kuruldu bildirimi
  Future<void> announceConnected() => speak('Drone bağlantısı kuruldu');

  /// Bağlantı kesildi bildirimi
  Future<void> announceDisconnected() => speak('Drone bağlantısı kesildi');

  /// Hata bildirimi
  Future<void> announceError(String error) => speak('Hata: $error');

  /// Tanınmayan komut bildirimi
  Future<void> announceUnknownCommand() =>
      speak('Komut anlaşılamadı, lütfen tekrar söyleyin');

  /// Debug log mesajı yazdırır.
  void _log(String message) {
    // ignore: avoid_print
    print('[TtsService] $message');
  }

  /// Servisi kapatır ve kaynakları serbest bırakır.
  Future<void> dispose() async {
    await stop();
    // FlutterTts'in doğrudan dispose metodu yok, stop yeterli
  }
}
