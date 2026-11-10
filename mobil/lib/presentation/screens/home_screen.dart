import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drone_voice_control/core/constants/app_constants.dart';
import 'package:drone_voice_control/core/theme/app_colors.dart';
import 'package:drone_voice_control/domain/repositories/settings_repository.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_event.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_state.dart';
import 'package:drone_voice_control/presentation/screens/flight_screen.dart';
import 'package:drone_voice_control/presentation/screens/settings_screen.dart';
import 'package:drone_voice_control/presentation/screens/flight_log_screen.dart';
import 'package:drone_voice_control/presentation/widgets/connection_indicator.dart';
import 'package:drone_voice_control/presentation/widgets/drone_status_card.dart';
import 'package:drone_voice_control/di/injection_container.dart';
import 'package:drone_voice_control/durum/telsiz_kontrolcusu.dart';
import 'package:drone_voice_control/ekranlar/telsiz_ekrani.dart';
import 'package:drone_voice_control/ekranlar/baglan_ekrani.dart';

class HomeScreen extends StatefulWidget {
  final TelsizKontrolcusu? telsizKontrolcusu;
  const HomeScreen({super.key, this.telsizKontrolcusu});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _hostController = TextEditingController();
  final TextEditingController _portController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final settingsRepo = sl<SettingsRepository>();
    final host = await settingsRepo.getRosbridgeHost();
    final port = await settingsRepo.getRosbridgePort();
    setState(() {
      _hostController.text = host;
      _portController.text = port.toString();
    });
  }

  @override
  void dispose() {
    _hostController.dispose();
    _portController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.flight_takeoff, color: AppColors.primary),
            SizedBox(width: 10),
            Text('DroneVoice', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: BlocConsumer<DroneBloc, DroneState>(
        listener: (context, state) {
          if (state is DroneConnected) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Gazebo Sim & ROS 2 Drone Bağlandı!'),
                backgroundColor: AppColors.success,
              ),
            );
          } else if (state is DroneError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.error,
              ),
            );
          }
        },
        builder: (context, state) {
          final isConnected = state is DroneConnected || state is DroneCommandSent;
          final isConnecting = state is DroneConnecting;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.defaultPadding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Bağlantı kartı
                Card(
                  color: AppColors.surface,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppConstants.defaultBorderRadius),
                    side: BorderSide(
                      color: isConnected ? AppColors.success : AppColors.border,
                    ),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Expanded(
                              child: Text(
                                'ROS 2 / Gazebo Köprüsü',
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textPrimary,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 8),
                            ConnectionIndicator(isConnected: isConnected),
                          ],
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _hostController,
                          decoration: const InputDecoration(
                            labelText: 'Rosbridge IP (Simülasyon PC)',
                            prefixIcon: Icon(Icons.computer),
                            hintText: '192.168.1.xxx veya localhost',
                          ),
                          enabled: !isConnected && !isConnecting,
                        ),
                        const SizedBox(height: 10),
                        TextField(
                          controller: _portController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: 'WebSocket Port (Varsayılan 9090)',
                            prefixIcon: Icon(Icons.settings_ethernet),
                          ),
                          enabled: !isConnected && !isConnecting,
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: isConnecting
                              ? null
                              : () {
                                  if (isConnected) {
                                    context.read<DroneBloc>().add(const DisconnectDrone());
                                  } else {
                                    final host = _hostController.text.trim();
                                    final port = int.tryParse(_portController.text.trim()) ?? 9090;
                                    context.read<DroneBloc>().add(
                                          ConnectDrone(host: host, port: port),
                                        );
                                  }
                                },
                          icon: isConnecting
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : Icon(isConnected ? Icons.link_off : Icons.link),
                          label: Text(
                            isConnecting
                                ? 'Bağlanıyor...'
                                : isConnected
                                    ? 'Bağlantıyı Kes'
                                    : 'Drone\'a Bağlan',
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: isConnected ? AppColors.error : AppColors.primary,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Drone Durum Kartı
                const DroneStatusCard(),
                const SizedBox(height: 20),

                // Uçuş Kontrolüne Git Butonu
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const FlightScreen()),
                    );
                  },
                  icon: const Icon(Icons.mic, size: 28),
                  label: const Text(
                    'SESLİ UÇUŞ KONTROL PANELİ',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 18),
                  ),
                ),
                const SizedBox(height: 14),

                // Uçuş Günlüğü Butonu
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const FlightLogScreen()),
                    );
                  },
                  icon: const Icon(Icons.history),
                  label: const Text('Uçuş Geçmişi & Loglar'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
                const SizedBox(height: 14),

                // Telsiz / PTT Modülü Butonu
                if (widget.telsizKontrolcusu != null)
                  ElevatedButton.icon(
                    onPressed: () {
                      final kontrolcu = widget.telsizKontrolcusu!;
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ListenableBuilder(
                            listenable: kontrolcu,
                            builder: (context, _) => kontrolcu.bagliOldu
                                ? TelsizEkrani(kontrolcu: kontrolcu)
                                : BaglanEkrani(kontrolcu: kontrolcu),
                          ),
                        ),
                      );
                    },
                    icon: const Icon(Icons.radio, size: 26),
                    label: const Text(
                      'DRONE TELSİZİ (BAS-KONUŞ)',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}

