import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:drone_voice_control/core/theme/app_colors.dart';
import 'package:drone_voice_control/core/utils/connection_log.dart';
import 'package:drone_voice_control/data/datasources/rosbridge_service.dart';
import 'package:drone_voice_control/di/injection_container.dart';

/// Rosbridge iletişim günlüğü.
///
/// Gösterilenler: WebSocket bağlantı durumu, advertise/publish çerçeveleri,
/// heartbeat gidiş-dönüş yanıtı (`/rosapi/get_time`, ms), rosbridge `status`
/// hataları ve backend'den gelen `/drone/feedback` mesajları. Bir metnin
/// backend'e ulaştığının kesin göstergesi, gönderimden sonra gelen
/// `backend` kaydıdır (command_parser veya mission_executor yanıtı).
class ConnectionLogScreen extends StatefulWidget {
  const ConnectionLogScreen({super.key});

  @override
  State<ConnectionLogScreen> createState() => _ConnectionLogScreenState();
}

class _ConnectionLogScreenState extends State<ConnectionLogScreen> {
  final ConnectionLog _log = sl<ConnectionLog>();
  final RosbridgeService _ros = sl<RosbridgeService>();

  /// null = tüm seviyeler
  LogLevel? _filter;

  static Color _color(LogLevel level) => switch (level) {
        LogLevel.info => AppColors.textSecondary,
        LogLevel.success => const Color(0xFF00E676),
        LogLevel.warning => const Color(0xFFFFC400),
        LogLevel.error => const Color(0xFFFF5252),
      };

  static IconData _icon(LogLevel level) => switch (level) {
        LogLevel.info => Icons.info_outline,
        LogLevel.success => Icons.check_circle_outline,
        LogLevel.warning => Icons.warning_amber,
        LogLevel.error => Icons.error_outline,
      };

  Future<void> _copy() async {
    await Clipboard.setData(ClipboardData(text: _log.export()));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Günlük panoya kopyalandı')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('İletişim Günlüğü'),
        actions: [
          IconButton(
            tooltip: 'Kopyala',
            icon: const Icon(Icons.copy),
            onPressed: _copy,
          ),
          IconButton(
            tooltip: 'Temizle',
            icon: const Icon(Icons.delete_outline),
            onPressed: _log.clear,
          ),
        ],
      ),
      body: Column(
        children: [
          // Anlık bağlantı durumu
          StreamBuilder<RosbridgeConnectionState>(
            stream: _ros.connectionStateStream,
            initialData: _ros.currentState,
            builder: (context, snap) {
              final state = snap.data ?? RosbridgeConnectionState.disconnected;
              final connected = state == RosbridgeConnectionState.connected;
              final address =
                  _ros.host == null ? '-' : 'ws://${_ros.host}:${_ros.port}';
              return Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                color: AppColors.surface,
                child: Row(
                  children: [
                    Icon(Icons.circle,
                        size: 12,
                        color: connected
                            ? const Color(0xFF00E676)
                            : const Color(0xFFFF5252)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${state.name.toUpperCase()}  •  $address',
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          // Seviye filtresi
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              children: [
                _chip('Tümü', null),
                for (final level in LogLevel.values) _chip(level.name, level),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListenableBuilder(
              listenable: _log,
              builder: (context, _) {
                final items = _log.entries.reversed
                    .where((e) => _filter == null || e.level == _filter)
                    .toList();
                if (items.isEmpty) {
                  return const Center(
                    child: Text('Kayıt yok',
                        style: TextStyle(color: AppColors.textSecondary)),
                  );
                }
                return ListView.separated(
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final e = items[i];
                    final color = _color(e.level);
                    return ListTile(
                      dense: true,
                      leading: Icon(_icon(e.level), color: color, size: 20),
                      title: SelectableText(
                        e.message,
                        style: const TextStyle(
                            fontFamily: 'monospace', fontSize: 12),
                      ),
                      subtitle: Text(
                        '${e.time.toIso8601String().substring(11, 23)}  •  ${e.source}',
                        style: TextStyle(color: color, fontSize: 11),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _chip(String label, LogLevel? level) => Padding(
        padding: const EdgeInsets.only(right: 6),
        child: ChoiceChip(
          label: Text(label),
          selected: _filter == level,
          onSelected: (_) => setState(() => _filter = level),
        ),
      );
}
