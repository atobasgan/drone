/// ConnectionLog - Rosbridge iletişiminin uygulama içi günlüğü.
///
/// Bağlantı durumları, gönderilen çerçeveler (advertise/publish), rosbridge
/// yanıtları (service_response, status) ve backend geri bildirimleri buraya
/// yazılır. Kayıtlar bellekte tutulur, en fazla [capacity] adet saklanır.
library;

import 'package:flutter/foundation.dart';

enum LogLevel { info, success, warning, error }

/// Günlükteki tek bir kayıt.
class LogEntry {
  final DateTime time;
  final LogLevel level;

  /// Kaydı üreten katman (ör. "bağlantı", "gönderim", "backend")
  final String source;
  final String message;

  const LogEntry({
    required this.time,
    required this.level,
    required this.source,
    required this.message,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is LogEntry &&
          other.time == time &&
          other.level == level &&
          other.source == source &&
          other.message == message;

  @override
  int get hashCode => Object.hash(time, level, source, message);

  @override
  String toString() {
    final t = time.toIso8601String().substring(11, 23);
    return '$t [${level.name.toUpperCase()}] $source: $message';
  }
}

class ConnectionLog extends ChangeNotifier {
  ConnectionLog({this.capacity = 500});

  final int capacity;
  final List<LogEntry> _entries = [];

  /// Kayıtlar, eskiden yeniye.
  List<LogEntry> get entries => List.unmodifiable(_entries);

  void add(LogLevel level, String source, String message) {
    _entries.add(LogEntry(
      time: DateTime.now(),
      level: level,
      source: source,
      message: message,
    ));
    if (_entries.length > capacity) _entries.removeAt(0);
    if (kDebugMode) debugPrint('[ConnectionLog] ${_entries.last}');
    notifyListeners();
  }

  void info(String source, String message) => add(LogLevel.info, source, message);
  void success(String source, String message) => add(LogLevel.success, source, message);
  void warning(String source, String message) => add(LogLevel.warning, source, message);
  void error(String source, String message) => add(LogLevel.error, source, message);

  void clear() {
    _entries.clear();
    notifyListeners();
  }

  /// Panoya kopyalamak için tüm günlük, satır satır.
  String export() => _entries.map((e) => e.toString()).join('\n');
}
