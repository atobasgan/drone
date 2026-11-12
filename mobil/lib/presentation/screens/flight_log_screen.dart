import 'package:flutter/material.dart';
import 'package:drone_voice_control/core/constants/app_constants.dart';
import 'package:drone_voice_control/core/theme/app_colors.dart';

class FlightLogScreen extends StatelessWidget {
  const FlightLogScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Örnek simülasyon geçmişi
    final logs = [
      {
        'date': '2026-10-20 14:15',
        'duration': '3 dk 42 sn',
        'commands': 18,
        'status': 'Başarılı İniş',
      },
      {
        'date': '2026-10-20 13:50',
        'duration': '1 dk 15 sn',
        'commands': 6,
        'status': 'Hover / Durduruldu',
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Uçuş Geçmişi'),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(AppConstants.defaultPadding),
        itemCount: logs.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final log = logs[index];
          return Card(
            color: AppColors.surface,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
              side: const BorderSide(color: AppColors.border),
            ),
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: AppColors.primary,
                child: Icon(Icons.flight, color: Colors.white),
              ),
              title: Text(
                log['date'] as String,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Text(
                'Süre: ${log['duration']} • ${log['commands']} Komut\nDurum: ${log['status']}',
              ),
              isThreeLine: true,
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                // Detay dialogu
                showDialog(
                  context: context,
                  builder: (_) => AlertDialog(
                    title: Text('Uçuş Detayı - ${log['date']}'),
                    content: Text(
                      'Uçuş Süresi: ${log['duration']}\n'
                      'Toplam Komut Sayısı: ${log['commands']}\n'
                      'Son Durum: ${log['status']}\n\n'
                      'Hedef: Gazebo Sim drone_world.sdf\n'
                      'Topic: /drone/cmd_vel (Twist)',
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Kapat'),
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

