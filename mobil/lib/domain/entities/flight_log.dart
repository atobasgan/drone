/// FlightLog - Uçuş kaydını temsil eden entity.
///
/// Bir uçuş seansı boyunca gönderilen tüm komutların,
/// başlangıç ve bitiş zamanlarının kaydını tutar.
library;

import 'drone_command.dart';

/// Uçuş kaydı entity sınıfı.
///
/// Bir oturumdaki tüm drone komutlarını kronolojik sırayla saklar.
/// Uçuş süresi, komut sayısı gibi özet bilgilere erişim sağlar.
class FlightLog {
  /// Benzersiz kayıt kimliği
  final String id;

  /// Uçuş boyunca gönderilen komutların listesi (kronolojik sıralı)
  final List<DroneCommand> commands;

  /// Uçuşun başlangıç zamanı
  final DateTime startTime;

  /// Uçuşun bitiş zamanı (uçuş devam ediyorsa `null`)
  final DateTime? endTime;

  const FlightLog({
    required this.id,
    required this.commands,
    required this.startTime,
    this.endTime,
  });

  /// Boş bir uçuş kaydı oluşturur (yeni oturum başlatmak için).
  factory FlightLog.start() => FlightLog(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        commands: const [],
        startTime: DateTime.now(),
      );

  /// Uçuş süresi.
  /// Uçuş devam ediyorsa şu ana kadar geçen süreyi döndürür.
  Duration get duration {
    final end = endTime ?? DateTime.now();
    return end.difference(startTime);
  }

  /// Toplam komut sayısı
  int get commandCount => commands.length;

  /// Uçuşun devam edip etmediği
  bool get isActive => endTime == null;

  /// Kayda yeni bir komut ekleyerek güncellenmiş kopya döndürür.
  FlightLog addCommand(DroneCommand command) {
    return FlightLog(
      id: id,
      commands: [...commands, command],
      startTime: startTime,
      endTime: endTime,
    );
  }

  /// Uçuşu bitirir ve bitiş zamanını ayarlar.
  FlightLog finish() {
    return FlightLog(
      id: id,
      commands: commands,
      startTime: startTime,
      endTime: DateTime.now(),
    );
  }

  @override
  String toString() =>
      'FlightLog(id: $id, komut sayısı: $commandCount, '
      'süre: ${duration.inSeconds}s, aktif: $isActive)';
}
