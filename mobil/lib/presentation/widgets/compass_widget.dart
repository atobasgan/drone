import 'dart:math' as math;
import 'package:flutter/material.dart';

/// Pusula widget'ı - drone yönünü gösterir
///
/// Telemetriden gelen yaw açısına göre dönen
/// bir pusula ibresi gösterir.
class CompassWidget extends StatelessWidget {
  /// Drone'un yaw açısı (radyan)
  final double headingRadians;

  /// Widget boyutu
  final double size;

  const CompassWidget({
    super.key,
    double? headingRadians,
    double? yaw,
    this.size = 100,
  }) : headingRadians = yaw ?? headingRadians ?? 0.0;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _CompassPainter(
          headingRadians: headingRadians,
        ),
      ),
    );
  }
}

class _CompassPainter extends CustomPainter {
  final double headingRadians;

  _CompassPainter({required this.headingRadians});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;

    // Dış halka
    final outerRingPaint = Paint()
      ..color = const Color(0xFF2A2A3C)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, radius, outerRingPaint);

    // Dış çerçeve
    final borderPaint = Paint()
      ..color = const Color(0xFF00E5FF).withValues(alpha: 0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    canvas.drawCircle(center, radius, borderPaint);

    // Yön çizgileri (N, E, S, W)
    _drawDirectionMarkers(canvas, center, radius);

    // Pusula ibresi
    _drawNeedle(canvas, center, radius * 0.65);

    // Merkez noktası
    final centerDotPaint = Paint()
      ..color = const Color(0xFF00E5FF)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, 4, centerDotPaint);
  }

  void _drawDirectionMarkers(Canvas canvas, Offset center, double radius) {
    final directions = ['K', 'D', 'G', 'B']; // Kuzey, Doğu, Güney, Batı
    final angles = [0.0, math.pi / 2, math.pi, 3 * math.pi / 2];

    for (int i = 0; i < directions.length; i++) {
      final angle = angles[i] - math.pi / 2; // Kuzey üstte olacak şekilde

      // Yön çizgisi
      final innerPoint = Offset(
        center.dx + (radius - 12) * math.cos(angle),
        center.dy + (radius - 12) * math.sin(angle),
      );
      final outerPoint = Offset(
        center.dx + (radius - 4) * math.cos(angle),
        center.dy + (radius - 4) * math.sin(angle),
      );

      final tickPaint = Paint()
        ..color = i == 0
            ? const Color(0xFFFF5252) // Kuzey kırmızı
            : Colors.grey.shade500
        ..strokeWidth = i == 0 ? 2.5 : 1.5;
      canvas.drawLine(innerPoint, outerPoint, tickPaint);

      // Yön harfi
      final textPainter = TextPainter(
        text: TextSpan(
          text: directions[i],
          style: TextStyle(
            color: i == 0
                ? const Color(0xFFFF5252)
                : Colors.grey.shade400,
            fontSize: radius * 0.2,
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();
      final textOffset = Offset(
        center.dx + (radius - 24) * math.cos(angle) - textPainter.width / 2,
        center.dy + (radius - 24) * math.sin(angle) - textPainter.height / 2,
      );
      textPainter.paint(canvas, textOffset);

      // Ara çizgiler (45 derece araları)
      final subAngle = angles[i] + math.pi / 4 - math.pi / 2;
      final subInner = Offset(
        center.dx + (radius - 8) * math.cos(subAngle),
        center.dy + (radius - 8) * math.sin(subAngle),
      );
      final subOuter = Offset(
        center.dx + (radius - 4) * math.cos(subAngle),
        center.dy + (radius - 4) * math.sin(subAngle),
      );
      final subTickPaint = Paint()
        ..color = Colors.grey.shade600
        ..strokeWidth = 1;
      canvas.drawLine(subInner, subOuter, subTickPaint);
    }
  }

  void _drawNeedle(Canvas canvas, Offset center, double length) {
    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(-headingRadians); // Drone yönüne göre döndür

    // Kuzey ibresi (kırmızı)
    final northPath = Path()
      ..moveTo(0, -length)
      ..lineTo(-6, 0)
      ..lineTo(6, 0)
      ..close();
    final northPaint = Paint()
      ..color = const Color(0xFFFF5252)
      ..style = PaintingStyle.fill;
    canvas.drawPath(northPath, northPaint);

    // Güney ibresi (beyaz)
    final southPath = Path()
      ..moveTo(0, length * 0.6)
      ..lineTo(-5, 0)
      ..lineTo(5, 0)
      ..close();
    final southPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.6)
      ..style = PaintingStyle.fill;
    canvas.drawPath(southPath, southPaint);

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _CompassPainter oldDelegate) {
    return oldDelegate.headingRadians != headingRadians;
  }
}
