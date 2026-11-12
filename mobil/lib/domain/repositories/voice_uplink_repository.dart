/// VoiceUplinkRepository - Ses kaydını ve ham metni backend'e ileten arayüz.
///
/// Mobil uygulama ne sesi yazıya çevirir ne de metni yorumlar:
///   - ses kaydı → `/voice/audio` (backend STT modeli metne çevirir)
///   - hazır metin (hızlı komut düğmeleri, DURDUR) → `/voice/text`
library;

import '../entities/audio_clip.dart';
import '../entities/backend_feedback.dart';

abstract class VoiceUplinkRepository {
  /// [clip] kaydını WAV dosyası olarak `/voice/audio` konusuna yayınlar.
  ///
  /// Kayıt boşsa ya da rosbridge bağlantısı yoksa gönderilmez ve `false` döner.
  bool sendAudioClip(AudioClip clip);

  /// [text] değerini değiştirmeden `/voice/text` konusuna yayınlar.
  ///
  /// Metin boşsa ya da bağlantı yoksa gönderilmez ve `false` döner.
  bool sendRawText(String text);

  /// `/voice/text` konusundaki metinler: backend STT'nin sesten ürettiği metin
  /// (ve bu uygulamanın kendi gönderdiği metinler).
  Stream<String> get transcriptStream;

  /// `/drone/feedback` konusundan gelen backend geri bildirimleri.
  Stream<BackendFeedback> get feedbackStream;
}
