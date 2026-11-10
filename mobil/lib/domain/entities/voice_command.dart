/// VoiceCommand - Sesli komut verisini temsil eden entity.
///
/// Kullanıcının mikrofon aracılığıyla söylediği komutu,
/// ham metin, güvenilirlik skoru ve ayrıştırılmış drone komutu
/// bilgileriyle birlikte tutar.
library;

import 'drone_command.dart';

/// Sesli komut entity sınıfı.
///
/// Ses tanıma sürecinin sonucunu temsil eder:
/// - [rawText]: Tanınan ham metin (ör. "ileri git", "yukarı çık")
/// - [confidence]: Tanıma güvenilirlik skoru (0.0 – 1.0)
/// - [parsedCommand]: Metinden ayrıştırılan DroneCommand (varsa)
/// - [isValid]: Komutun geçerli bir drone komutu olup olmadığı
class VoiceCommand {
  /// Ses tanıma motorunun döndürdüğü ham metin
  final String rawText;

  /// Tanıma güvenilirlik skoru (0.0 = en düşük, 1.0 = en yüksek)
  final double confidence;

  /// Ham metinden ayrıştırılmış drone komutu.
  /// Metin geçerli bir komut değilse `null` olur.
  final DroneCommand? parsedCommand;

  /// Komutun oluşturulma zamanı
  final DateTime timestamp;

  /// Komutun geçerli ve uygulanabilir olup olmadığı
  final bool isValid;

  /// Tanımanın tamamlanıp tamamlanmadığı (ara sonuç / final)
  final bool isFinal;

  const VoiceCommand({
    required this.rawText,
    this.confidence = 0.0,
    this.parsedCommand,
    required this.timestamp,
    this.isValid = false,
    this.isFinal = true,
  });

  /// Boş / tanınmamış bir sesli komut oluşturur.
  factory VoiceCommand.empty() => VoiceCommand(
        rawText: '',
        confidence: 0.0,
        parsedCommand: null,
        timestamp: DateTime.now(),
        isValid: false,
        isFinal: true,
      );

  /// Komutun güvenilirlik eşiğini aşıp aşmadığını kontrol eder.
  /// Varsayılan eşik: 0.5 (%50)
  bool isConfident({double threshold = 0.5}) => confidence >= threshold;

  /// Komutun hem geçerli hem de yeterince güvenilir olup olmadığını kontrol eder.
  bool get isActionable => isValid && isConfident() && parsedCommand != null;

  /// Mevcut sesli komutu kısmen güncelleyerek yeni bir kopya oluşturur.
  VoiceCommand copyWith({
    String? rawText,
    double? confidence,
    DroneCommand? parsedCommand,
    DateTime? timestamp,
    bool? isValid,
  }) {
    return VoiceCommand(
      rawText: rawText ?? this.rawText,
      confidence: confidence ?? this.confidence,
      parsedCommand: parsedCommand ?? this.parsedCommand,
      timestamp: timestamp ?? this.timestamp,
      isValid: isValid ?? this.isValid,
    );
  }

  @override
  String toString() =>
      'VoiceCommand("$rawText", güvenilirlik: $confidence, '
      'geçerli: $isValid, komut: $parsedCommand)';
}
