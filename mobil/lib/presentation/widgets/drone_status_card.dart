import 'package:flutter/material.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';

/// Drone durum bilgisi kartı
///
/// Uçuş durumu, batarya (simüle), yükseklik ve hız
/// bilgilerini kompakt bir kart olarak gösterir.
class DroneStatusCard extends StatelessWidget {
  /// Drone telemetri verisi
  final DroneTelemetry? telemetry;

  /// Drone bağlı mı?
  final bool isConnected;

  const DroneStatusCard({
    super.key,
    this.telemetry,
    this.isConnected = false,
  });

  /// Uçuş durumuna göre renk
  Color _getStatusColor() {
    if (!isConnected) return Colors.grey;
    if (telemetry == null) return Colors.orange;

    final altitude = telemetry!.position.z;
    if (altitude > 0.5) return const Color(0xFF00E676); // Uçuyor - yeşil
    return const Color(0xFF00B0FF); // Yerde - mavi
  }

  /// Uçuş durumu metni
  String _getFlightStateText() {
    if (!isConnected) return 'Bağlantı Yok';
    if (telemetry == null) return 'Bekleniyor...';

    final altitude = telemetry!.position.z;
    if (altitude > 0.5) return 'Uçuşta';
    return 'Yerde';
  }

  /// Simüle edilmiş batarya yüzdesi
  int _getSimulatedBattery() {
    // Gerçek batarya verisi olmadığından simüle ediyoruz
    return 85;
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor();
    final speed = telemetry != null
        ? _calculateSpeed(telemetry!.velocity)
        : 0.0;
    final altitude = telemetry?.position.z ?? 0.0;
    final battery = _getSimulatedBattery();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E2C),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: statusColor.withValues(alpha: 0.3),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: statusColor.withValues(alpha: 0.1),
            blurRadius: 12,
            spreadRadius: 1,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Başlık ve durum
          Row(
            children: [
              // Durum göstergesi noktası
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: statusColor,
                  boxShadow: [
                    BoxShadow(
                      color: statusColor.withValues(alpha: 0.5),
                      blurRadius: 6,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text(
                _getFlightStateText(),
                style: TextStyle(
                  color: statusColor,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              // Batarya göstergesi
              _buildBatteryIndicator(battery),
            ],
          ),
          const SizedBox(height: 16),
          // Metrik satırı
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildMetricTile(
                icon: Icons.height,
                label: 'Yükseklik',
                value: '${altitude.toStringAsFixed(1)} m',
                color: const Color(0xFF00E5FF),
              ),
              _buildMetricTile(
                icon: Icons.speed,
                label: 'Hız',
                value: '${speed.toStringAsFixed(1)} m/s',
                color: const Color(0xFF76FF03),
              ),
              _buildMetricTile(
                icon: Icons.explore,
                label: 'Yön',
                value: '${(telemetry?.heading ?? 0).toStringAsFixed(0)}°',
                color: const Color(0xFFFFD740),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Hız büyüklüğünü hesapla
  double _calculateSpeed(Vector3 velocity) {
    final vx = velocity.x;
    final vy = velocity.y;
    final vz = velocity.z;
    return (vx * vx + vy * vy + vz * vz).abs() < 0.001
        ? 0.0
        : _sqrt(vx * vx + vy * vy + vz * vz);
  }

  /// Basit karekök (dart:math importu yerine)
  double _sqrt(double value) {
    if (value <= 0) return 0;
    double guess = value / 2;
    for (int i = 0; i < 20; i++) {
      guess = (guess + value / guess) / 2;
    }
    return guess;
  }

  /// Batarya göstergesi
  Widget _buildBatteryIndicator(int percentage) {
    Color batteryColor;
    if (percentage > 60) {
      batteryColor = const Color(0xFF00E676);
    } else if (percentage > 30) {
      batteryColor = const Color(0xFFFFD740);
    } else {
      batteryColor = const Color(0xFFFF1744);
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          percentage > 60
              ? Icons.battery_full
              : percentage > 30
                  ? Icons.battery_3_bar
                  : Icons.battery_1_bar,
          color: batteryColor,
          size: 20,
        ),
        const SizedBox(width: 4),
        Text(
          '%$percentage',
          style: TextStyle(
            color: batteryColor,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  /// Tek metrik tile widget'ı
  Widget _buildMetricTile({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: color, size: 22),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            color: Colors.grey.shade500,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}
