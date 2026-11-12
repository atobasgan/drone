/// AudioClip - Bas-konuş ile kaydedilen tek bir konuşmanın ham sesi.
///
/// İçerik 16 bit işaretli, little-endian PCM örnekleridir. Mobil uygulama
/// sesi yazıya çevirmez; bu kayıt backend'e gönderilir ve konuşma tanıma
/// orada yapılır.
library;

import 'dart:typed_data';

class AudioClip {
  /// PCM16 LE örnekleri
  final Uint8List pcm;

  /// Örnekleme hızı (Hz)
  final int sampleRate;

  /// Kanal sayısı
  final int channels;

  const AudioClip({
    required this.pcm,
    required this.sampleRate,
    this.channels = 1,
  });

  /// Kayıt süresi (ms). PCM16: örnek başına 2 bayt.
  int get durationMs => sampleRate == 0
      ? 0
      : pcm.length * 1000 ~/ (sampleRate * channels * 2);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    if (other is! AudioClip ||
        other.sampleRate != sampleRate ||
        other.channels != channels ||
        other.pcm.length != pcm.length) {
      return false;
    }
    for (var i = 0; i < pcm.length; i++) {
      if (other.pcm[i] != pcm[i]) return false;
    }
    return true;
  }

  /// Bayt içeriği hash'e katılmaz (yüz binlerce bayt); eşit nesneler yine
  /// eşit hash üretir, çünkü uzunluk ve biçim eşitliğin parçasıdır.
  @override
  int get hashCode => Object.hash(sampleRate, channels, pcm.length);

  @override
  String toString() =>
      'AudioClip($durationMs ms, ${pcm.length} bayt, $sampleRate Hz, $channels kanal)';
}
