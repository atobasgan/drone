import 'package:flutter/material.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';

/// Gerçek zamanlı telemetri gösterge paneli
///
/// Drone'un pozisyon, hız ve açısal hız verilerini
/// görsel olarak gösterir.
class TelemetryDisplay extends StatelessWidget {
  /// Telemetri verisi
  final DroneTelemetry? telemetry;

  const TelemetryDisplay({
    super.key,
    this.telemetry,
  });

  @override
  Widget build(BuildContext context) {
    final pos = telemetry?.position ?? const Vector3(x: 0, y: 0, z: 0);
    final vel = telemetry?.velocity ?? const Vector3(x: 0, y: 0, z: 0);
    final yawRate = telemetry?.yawRate ?? 0.0;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E2C),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: const Color(0xFF00E5FF).withValues(alpha: 0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Başlık
          Row(
            children: [
              const Icon(
                Icons.analytics_outlined,
                color: Color(0xFF00E5FF),
                size: 18,
              ),
              const SizedBox(width: 6),
              Text(
                'Telemetri',
                style: TextStyle(
                  color: Colors.grey.shade300,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Pozisyon satırı
          _buildSectionLabel('Pozisyon (m)'),
          const SizedBox(height: 4),
          Row(
            children: [
              _buildValueCell('X', pos.x, const Color(0xFFFF5252)),
              _buildValueCell('Y', pos.y, const Color(0xFF69F0AE)),
              _buildValueCell('Z', pos.z, const Color(0xFF448AFF)),
            ],
          ),
          const SizedBox(height: 12),

          // Hız satırı
          _buildSectionLabel('Hız (m/s)'),
          const SizedBox(height: 4),
          Row(
            children: [
              _buildValueCell('Vx', vel.x, const Color(0xFFFF5252)),
              _buildValueCell('Vy', vel.y, const Color(0xFF69F0AE)),
              _buildValueCell('Vz', vel.z, const Color(0xFF448AFF)),
            ],
          ),
          const SizedBox(height: 12),

          // Açısal hız (Yaw)
          Row(
            children: [
              _buildSectionLabel('Dönüş Hızı'),
              const Spacer(),
              Text(
                '${yawRate.toStringAsFixed(2)} rad/s',
                style: const TextStyle(
                  color: Color(0xFFFFD740),
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'monospace',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Yükseklik çubuğu göstergesi
          _buildAltitudeBar(pos.z),
        ],
      ),
    );
  }

  /// Bölüm etiketi
  Widget _buildSectionLabel(String label) {
    return Text(
      label,
      style: TextStyle(
        color: Colors.grey.shade500,
        fontSize: 11,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.5,
      ),
    );
  }

  /// Tek değer hücresi
  Widget _buildValueCell(String label, double value, Color color) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 2),
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: TextStyle(
                color: color.withValues(alpha: 0.7),
                fontSize: 10,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              value.toStringAsFixed(2),
              style: TextStyle(
                color: color,
                fontSize: 16,
                fontWeight: FontWeight.bold,
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Görsel yükseklik çubuğu göstergesi
  Widget _buildAltitudeBar(double altitude) {
    // Maksimum gösterim yüksekliği (metre)
    const maxDisplayAltitude = 50.0;
    final normalizedAlt = (altitude / maxDisplayAltitude).clamp(0.0, 1.0);

    Color barColor;
    if (altitude > 30) {
      barColor = const Color(0xFFFF5252); // Yüksek - kırmızı
    } else if (altitude > 15) {
      barColor = const Color(0xFFFFD740); // Orta - sarı
    } else {
      barColor = const Color(0xFF00E5FF); // Düşük - cyan
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.height, color: Color(0xFF00E5FF), size: 14),
            const SizedBox(width: 4),
            Text(
              'Yükseklik: ${altitude.toStringAsFixed(1)} m',
              style: TextStyle(
                color: Colors.grey.shade400,
                fontSize: 11,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: normalizedAlt,
            minHeight: 8,
            backgroundColor: Colors.grey.shade800,
            valueColor: AlwaysStoppedAnimation<Color>(barColor),
          ),
        ),
      ],
    );
  }
}
