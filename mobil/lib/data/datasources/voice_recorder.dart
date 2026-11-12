/// VoiceRecorder - Bas-konuş süresince mikrofonu belleğe kaydeder.
///
/// Telsiz modülünün [SesKaynagi] arayüzünü (16 kHz mono PCM16, `record`
/// paketi) kullanır. Ses yazıya çevrilmez; [stop] kaydın tamamını döndürür.
library;

import 'dart:async';
import 'dart:typed_data';

import 'package:drone_voice_control/domain/entities/audio_clip.dart';
import 'package:drone_voice_control/protokol/mesajlar.dart' show orneklemeHz;
import 'package:drone_voice_control/ses/mikrofon.dart';

class VoiceRecorder {
  VoiceRecorder({
    required SesKaynagi source,
    this.maxDuration = const Duration(seconds: 15),
    this.tail = const Duration(milliseconds: 250),
  }) : _source = source;

  final SesKaynagi _source;

  /// Bu süreden sonra gelen ses atılır (mesaj boyutu sınırı).
  final Duration maxDuration;

  /// Düğme bırakıldıktan sonra kayda devam süresi: son hece kesilmesin.
  final Duration tail;

  final BytesBuilder _buffer = BytesBuilder(copy: false);
  bool _recording = false;

  bool get isRecording => _recording;

  int get _maxBytes => orneklemeHz * 2 * maxDuration.inMilliseconds ~/ 1000;

  /// Mikrofon izni yoksa ya da kayıt başlatılamazsa `false`.
  Future<bool> start() async {
    if (_recording) await cancel();
    if (!await _source.izinIste()) return false;
    _buffer.clear();
    // Bayrak mikrofon açılmadan kurulur: ilk parçalar kaybolmasın.
    _recording = true;
    try {
      await _source.ac((veri) {
        if (_recording && _buffer.length < _maxBytes) _buffer.add(veri);
      });
    } catch (_) {
      _recording = false;
      return false;
    }
    return true;
  }

  /// Kaydı bitirir ve kaydedilen sesi döndürür.
  Future<AudioClip> stop() async {
    if (_recording && tail > Duration.zero) await Future<void>.delayed(tail);
    _recording = false;
    await _source.kapat();
    var pcm = _buffer.takeBytes();
    if (pcm.length > _maxBytes) pcm = Uint8List.sublistView(pcm, 0, _maxBytes);
    // PCM16: tek sayıda bayt kalmasın
    if (pcm.length.isOdd) pcm = Uint8List.sublistView(pcm, 0, pcm.length - 1);
    return AudioClip(pcm: pcm, sampleRate: orneklemeHz);
  }

  /// Kaydı atar.
  Future<void> cancel() async {
    _recording = false;
    _buffer.clear();
    await _source.kapat();
  }
}
