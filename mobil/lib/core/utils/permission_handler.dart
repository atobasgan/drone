import 'package:permission_handler/permission_handler.dart';

import '../errors/exceptions.dart';
import '../utils/logger.dart';

/// Mikrofon izni yönetim sınıfı.
/// Ses tanıma için gerekli izinleri kontrol eder ve talep eder.
class AppPermissionHandler {
  /// Mikrofon iznini kontrol et ve gerekirse talep et.
  /// İzin verilmediyse [PermissionDeniedException] fırlatır.
  static Future<bool> requestMicrophonePermission() async {
    AppLogger.info('Mikrofon izni kontrol ediliyor...', tag: 'Permission');

    // Mevcut izin durumunu kontrol et
    final status = await Permission.microphone.status;
    AppLogger.debug('Mevcut mikrofon izin durumu: $status', tag: 'Permission');

    if (status.isGranted) {
      AppLogger.info('Mikrofon izni zaten verilmiş', tag: 'Permission');
      return true;
    }

    if (status.isPermanentlyDenied) {
      AppLogger.warning(
        'Mikrofon izni kalıcı olarak reddedilmiş. '
        'Kullanıcının ayarlardan izin vermesi gerekiyor.',
        tag: 'Permission',
      );
      throw const PermissionDeniedException(
        message: 'Mikrofon izni kalıcı olarak reddedildi. '
            'Lütfen uygulama ayarlarından mikrofon iznini açın.',
      );
    }

    // İzin talep et
    AppLogger.info('Mikrofon izni talep ediliyor...', tag: 'Permission');
    final result = await Permission.microphone.request();

    if (result.isGranted) {
      AppLogger.info('Mikrofon izni verildi ✓', tag: 'Permission');
      return true;
    }

    AppLogger.warning('Mikrofon izni reddedildi ✗', tag: 'Permission');
    throw const PermissionDeniedException(
      message: 'Ses tanıma için mikrofon iznine ihtiyaç var.',
    );
  }

  /// Mikrofon izninin verilip verilmediğini kontrol et (talep etmeden).
  static Future<bool> isMicrophonePermissionGranted() async {
    final status = await Permission.microphone.status;
    return status.isGranted;
  }

  /// Uygulama ayarlarını aç (izin kalıcı olarak reddedildiyse).
  static Future<bool> openSettings() async {
    AppLogger.info('Uygulama ayarları açılıyor...', tag: 'Permission');
    return await openAppSettings();
  }
}
