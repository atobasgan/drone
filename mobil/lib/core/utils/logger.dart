import 'package:flutter/foundation.dart';

/// Basit loglama yardımcı sınıfı.
/// Debug modda konsola log basar, release modda sessizdir.
class AppLogger {
  AppLogger._();

  static const String _tag = '🚁 DroneApp';

  /// Bilgi logu
  static void info(String message, {String? tag}) {
    _log('ℹ️', tag ?? _tag, message);
  }

  /// Uyarı logu
  static void warning(String message, {String? tag}) {
    _log('⚠️', tag ?? _tag, message);
  }

  /// Hata logu
  static void error(String message, {String? tag, Object? error, StackTrace? stackTrace}) {
    _log('❌', tag ?? _tag, message);
    if (error != null) {
      _log('❌', tag ?? _tag, 'Error: $error');
    }
    if (stackTrace != null) {
      _log('❌', tag ?? _tag, 'StackTrace: $stackTrace');
    }
  }

  /// Debug logu
  static void debug(String message, {String? tag}) {
    _log('🐛', tag ?? _tag, message);
  }

  /// ROS iletişim logu
  static void ros(String message, {String? tag}) {
    _log('🤖', tag ?? 'ROS', message);
  }

  /// Ses tanıma logu
  static void speech(String message, {String? tag}) {
    _log('🎤', tag ?? 'Speech', message);
  }

  /// Drone komut logu
  static void command(String message, {String? tag}) {
    _log('🎮', tag ?? 'Command', message);
  }

  /// Bağlantı logu
  static void connection(String message, {String? tag}) {
    _log('🔌', tag ?? 'Connection', message);
  }

  /// Temel log fonksiyonu — sadece debug modda çalışır
  static void _log(String emoji, String tag, String message) {
    if (kDebugMode) {
      final timestamp = DateTime.now().toIso8601String().substring(11, 23);
      print('$emoji [$timestamp] [$tag] $message');
    }
  }
}
