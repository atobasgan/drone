/// VoiceRepository - Ses tanıma işlemleri için soyut repository.
///
/// Domain katmanında tanımlanan bu arayüz, ses tanıma servisinin
/// nasıl çalıştığına dair hiçbir detay içermez. Uygulama detayları
/// data katmanındaki `VoiceRepositoryImpl` tarafından sağlanır.
library;

import '../entities/voice_command.dart';

/// Ses tanıma repository arayüzü.
///
/// Kullanıcının sesli komutlarını dinlemek ve metin olarak almak için
/// gerekli yöntemleri tanımlar.
abstract class VoiceRepository {
  /// Ses dinlemeyi başlatır.
  ///
  /// [locale] parametresi dil ayarını belirtir (varsayılan: tr_TR).
  /// Dinleme başarıyla başlarsa `true`, aksi halde `false` döndürür.
  Future<bool> startListening({
    String locale = 'tr_TR',
    void Function(VoiceCommand)? onResult,
    void Function(String)? onError,
  });

  /// Ses dinlemeyi durdurur.
  Future<void> stopListening();

  /// Tanınan sesli komutların akışı.
  ///
  /// Mikrofon aktifken, her tanınan metin parçası için
  /// bir [VoiceCommand] nesnesi yayınlar.
  Stream<VoiceCommand> get voiceStream;

  /// Ses tanıma servisinin kullanılabilir olup olmadığını kontrol eder.
  Future<bool> get isAvailable;

  /// Ses dinlemenin aktif olup olmadığını döndürür.
  bool get isListening;
}
