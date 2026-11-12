import 'package:flutter/material.dart';

/// Uygulama renk paleti.
/// Drone kontrol teması: Koyu arkaplan, yeşil/cyan vurgular.
class AppColors {
  AppColors._();

  // ── Ana Renkler ──
  static const Color primary = Color(0xFF00E676);       // Yeşil — ana vurgu
  static const Color primaryDark = Color(0xFF00C853);    // Koyu yeşil
  static const Color primaryLight = Color(0xFF69F0AE);   // Açık yeşil

  static const Color secondary = Color(0xFF00BCD4);      // Cyan — ikincil vurgu
  static const Color secondaryDark = Color(0xFF0097A7);   // Koyu cyan
  static const Color secondaryLight = Color(0xFF4DD0E1);  // Açık cyan

  // ── Arkaplan Renkleri ──
  static const Color background = Color(0xFF0D1117);      // Ana arkaplan (çok koyu)
  static const Color surface = Color(0xFF161B22);          // Kart / yüzey arkaplanı
  static const Color surfaceLight = Color(0xFF21262D);     // Daha açık yüzey
  static const Color surfaceElevated = Color(0xFF30363D);  // Yükseltilmiş yüzey

  // ── Metin Renkleri ──
  static const Color textPrimary = Color(0xFFF0F6FC);     // Ana metin
  static const Color textSecondary = Color(0xFF8B949E);    // İkincil metin
  static const Color textTertiary = Color(0xFF6E7681);     // Üçüncül metin
  static const Color textDisabled = Color(0xFF484F58);     // Devre dışı metin

  // ── Durum Renkleri ──
  static const Color success = Color(0xFF00E676);          // Başarılı / bağlı
  static const Color warning = Color(0xFFFFB300);          // Uyarı
  static const Color error = Color(0xFFFF5252);            // Hata / acil durum
  static const Color info = Color(0xFF29B6F6);             // Bilgi

  // ── Drone Durumu Renkleri ──
  static const Color droneGrounded = Color(0xFF8B949E);    // Yerde
  static const Color droneTakingOff = Color(0xFFFFB300);   // Kalkış
  static const Color droneHovering = Color(0xFF00E676);    // Hover
  static const Color droneFlying = Color(0xFF00BCD4);      // Uçuş
  static const Color droneLanding = Color(0xFFFF9800);     // İniş
  static const Color droneEmergency = Color(0xFFFF5252);   // Acil durum

  // ── Bağlantı Durumu Renkleri ──
  static const Color connected = Color(0xFF00E676);
  static const Color connecting = Color(0xFFFFB300);
  static const Color disconnected = Color(0xFF8B949E);
  static const Color connectionError = Color(0xFFFF5252);

  // ── Diğer ──
  static const Color accent = secondary;
  static const Color border = Color(0xFF30363D);
  static const Color cardBackground = surface;
  static const Color divider = Color(0xFF30363D);
  static const Color shadow = Color(0x40000000);
  static const Color overlay = Color(0x80000000);
  static const Color micActive = Color(0xFFFF5252);        // Mikrofon aktif
  static const Color micInactive = Color(0xFF8B949E);      // Mikrofon pasif
}
