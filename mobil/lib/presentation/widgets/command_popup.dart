import 'package:flutter/material.dart';
import 'package:drone_voice_control/domain/entities/drone_command.dart';

/// Eşleşen komutun ekranda ve sesli olarak nasıl duyurulacağı.
class KomutDuyurusu {
  /// Algılanan komutun adı (ör. "İleri", "Kalkış")
  final String komutAdi;

  /// Drone'un ne yaptığını anlatan cümle (ör. "İleri gidiliyor")
  final String cumle;

  /// Pop-up ikonu
  final IconData ikon;

  /// Kullanıcının söylediği ham metin
  final String soylenen;

  const KomutDuyurusu({
    required this.komutAdi,
    required this.cumle,
    required this.ikon,
    required this.soylenen,
  });

  /// Sesli okunacak tam metin: hem komutu hem yapılanı söyler.
  /// Ör. "İleri komutu alındı. İleri gidiliyor."
  String get sesliMetin => '$komutAdi komutu alındı. $cumle.';

  /// Komut tipine (ve kalkış/iniş için söylenen metne) göre duyuru üretir.
  factory KomutDuyurusu.komuttan(DroneCommand komut, String soylenen) {
    final metin = soylenen.toLowerCase();

    // Kalkış/iniş, yükselme/alçalma ile aynı komut tipine eşleniyor;
    // kullanıcı ne dediyse onu duysun.
    if (komut.commandType == DroneCommandType.moveUp &&
        metin.contains('kalk')) {
      return KomutDuyurusu(
        komutAdi: 'Kalkış',
        cumle: 'Kalkış yapılıyor',
        ikon: Icons.flight_takeoff,
        soylenen: soylenen,
      );
    }
    if (komut.commandType == DroneCommandType.moveDown &&
        metin.contains('iniş')) {
      return KomutDuyurusu(
        komutAdi: 'İniş',
        cumle: 'İniş yapılıyor',
        ikon: Icons.flight_land,
        soylenen: soylenen,
      );
    }

    final (komutAdi, cumle, ikon) = switch (komut.commandType) {
      DroneCommandType.moveForward => (
          'İleri',
          'İleri gidiliyor',
          Icons.arrow_upward
        ),
      DroneCommandType.moveBackward => (
          'Geri',
          'Geri gidiliyor',
          Icons.arrow_downward
        ),
      DroneCommandType.moveLeft => (
          'Sola git',
          'Sola gidiliyor',
          Icons.arrow_back
        ),
      DroneCommandType.moveRight => (
          'Sağa git',
          'Sağa gidiliyor',
          Icons.arrow_forward
        ),
      DroneCommandType.moveUp => (
          'Yüksel',
          'Yükseliniyor',
          Icons.keyboard_double_arrow_up
        ),
      DroneCommandType.moveDown => (
          'Alçal',
          'Alçalınıyor',
          Icons.keyboard_double_arrow_down
        ),
      DroneCommandType.rotateLeft => (
          'Sola dön',
          'Sola dönülüyor',
          Icons.rotate_left
        ),
      DroneCommandType.rotateRight => (
          'Sağa dön',
          'Sağa dönülüyor',
          Icons.rotate_right
        ),
      DroneCommandType.hover => (
          'Dur',
          'Durduruluyor, havada bekleniyor',
          Icons.pan_tool
        ),
      DroneCommandType.custom => (
          'Özel',
          'Komut uygulanıyor',
          Icons.check_circle
        ),
    };
    return KomutDuyurusu(
        komutAdi: komutAdi, cumle: cumle, ikon: ikon, soylenen: soylenen);
  }
}

/// Eşleşen komutu ekranın ortasında kısa süre gösteren pop-up kartı.
class CommandPopup extends StatelessWidget {
  final KomutDuyurusu duyuru;

  const CommandPopup({super.key, required this.duyuru});

  static const _yesil = Color(0xFF00E676);

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 320),
        margin: const EdgeInsets.symmetric(horizontal: 32),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 22),
        decoration: BoxDecoration(
          color: const Color(0xFF161B22),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: _yesil, width: 2),
          boxShadow: [
            BoxShadow(
              color: _yesil.withValues(alpha: 0.35),
              blurRadius: 30,
              spreadRadius: 4,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: _yesil.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(duyuru.ikon, color: _yesil, size: 44),
            ),
            const SizedBox(height: 14),
            Text(
              '${duyuru.komutAdi.toUpperCase()} KOMUTU ALINDI',
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: _yesil,
                fontSize: 12,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              duyuru.cumle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '"${duyuru.soylenen}"',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.grey.shade400,
                fontSize: 14,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
