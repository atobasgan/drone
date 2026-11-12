import 'package:flutter/material.dart';
import 'package:drone_voice_control/domain/entities/backend_feedback.dart';

/// Pop-up ve sesli okuma için gösterilecek içerik.
///
/// İçerik mobil tarafta komut çözülerek üretilmez: ya gönderilen ham metnin
/// iletildiğini bildirir ya da backend'in `/drone/feedback` mesajını taşır.
class KomutDuyurusu {
  /// Başlık (ör. "İLETİLDİ", "REDDEDİLDİ")
  final String baslik;

  /// Ana metin
  final String cumle;

  /// Pop-up ikonu
  final IconData ikon;

  /// Kullanıcının söylediği ham metin
  final String soylenen;

  /// Vurgu rengi
  final Color renk;

  const KomutDuyurusu({
    required this.baslik,
    required this.cumle,
    required this.ikon,
    required this.soylenen,
    this.renk = yesil,
  });

  static const Color yesil = Color(0xFF00E676);
  static const Color kirmizi = Color(0xFFFF5252);
  static const Color mavi = Color(0xFF40C4FF);

  /// Ham metin `/voice/text` konusuna yazıldı; backend cevabı bekleniyor.
  factory KomutDuyurusu.iletildi(String soylenen) => KomutDuyurusu(
        baslik: 'İletildi',
        cumle: 'Backend yanıtı bekleniyor',
        ikon: Icons.send,
        soylenen: soylenen,
        renk: mavi,
      );

  /// Ses kaydı `/voice/audio` konusuna yazıldı; backend STT bekleniyor.
  factory KomutDuyurusu.sesIletildi(int durationMs) => KomutDuyurusu(
        baslik: 'Ses gönderildi',
        cumle: 'Backend sesi yazıya çeviriyor',
        ikon: Icons.graphic_eq,
        soylenen: '${(durationMs / 1000).toStringAsFixed(1)} sn kayıt',
        renk: mavi,
      );

  /// Backend geri bildirimi; [BackendFeedback.mesaj] olduğu gibi gösterilir.
  factory KomutDuyurusu.geriBildirimden(BackendFeedback fb, String soylenen) {
    final (baslik, ikon) = switch (fb.durum) {
      'kabul' => ('Kabul edildi', Icons.check_circle),
      'yurutuyor' => ('Yürütülüyor', Icons.flight),
      'tamamlandi' => ('Tamamlandı', Icons.done_all),
      'reddedildi' => ('Reddedildi', Icons.block),
      'hata' => ('Hata', Icons.error),
      _ => ('Bilgi', Icons.info),
    };
    return KomutDuyurusu(
      baslik: baslik,
      cumle: fb.mesaj,
      ikon: ikon,
      soylenen: soylenen,
      renk: fb.isNegative ? kirmizi : yesil,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is KomutDuyurusu &&
          other.baslik == baslik &&
          other.cumle == cumle &&
          other.ikon == ikon &&
          other.soylenen == soylenen &&
          other.renk == renk;

  @override
  int get hashCode => Object.hash(baslik, cumle, ikon, soylenen, renk);

  @override
  String toString() => 'KomutDuyurusu($baslik: $cumle, "$soylenen")';
}

/// Gönderim ve backend sonucunu ekranın ortasında kısa süre gösteren kart.
class CommandPopup extends StatelessWidget {
  final KomutDuyurusu duyuru;

  const CommandPopup({super.key, required this.duyuru});

  @override
  Widget build(BuildContext context) {
    final renk = duyuru.renk;
    return Material(
      color: Colors.transparent,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 320),
        margin: const EdgeInsets.symmetric(horizontal: 32),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 22),
        decoration: BoxDecoration(
          color: const Color(0xFF161B22),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: renk, width: 2),
          boxShadow: [
            BoxShadow(
              color: renk.withValues(alpha: 0.35),
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
                color: renk.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(duyuru.ikon, color: renk, size: 44),
            ),
            const SizedBox(height: 14),
            Text(
              duyuru.baslik.toUpperCase(),
              textAlign: TextAlign.center,
              style: TextStyle(
                color: renk,
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
                fontSize: 20,
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
