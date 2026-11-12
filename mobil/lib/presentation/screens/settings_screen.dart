import 'package:flutter/material.dart';
import 'package:drone_voice_control/core/constants/app_constants.dart';
import 'package:drone_voice_control/core/theme/app_colors.dart';
import 'package:drone_voice_control/domain/repositories/settings_repository.dart';
import 'package:drone_voice_control/di/injection_container.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _hostController = TextEditingController();
  final _portController = TextEditingController();
  String _language = 'tr_TR';

  final _settingsRepo = sl<SettingsRepository>();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final host = await _settingsRepo.getRosbridgeHost();
    final port = await _settingsRepo.getRosbridgePort();
    final lang = await _settingsRepo.getLanguage();

    setState(() {
      _hostController.text = host;
      _portController.text = port.toString();
      _language = lang;
    });
  }

  Future<void> _saveSettings() async {
    await _settingsRepo.setRosbridgeHost(_hostController.text.trim());
    final port = int.tryParse(_portController.text.trim()) ?? 9090;
    await _settingsRepo.setRosbridgePort(port);
    await _settingsRepo.setLanguage(_language);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Ayarlar başarıyla kaydedildi!'),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.pop(context);
    }
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
        title: const Text('Ayarlar'),
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            onPressed: _saveSettings,
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppConstants.defaultPadding),
        children: [
          const Text(
            'ROS 2 / Gazebo Köprü Yapılandırması',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.accent),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _hostController,
            decoration: const InputDecoration(
              labelText: 'Rosbridge Sunucu IP Adresi',
              helperText: 'Örn: 192.168.1.105 (PC\'nin yerel IP adresi)',
              prefixIcon: Icon(Icons.wifi),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _portController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Rosbridge WebSocket Port',
              helperText: 'Varsayılan: 9090',
              prefixIcon: Icon(Icons.numbers),
            ),
          ),
          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 12),
          const Text(
            'Hız ve Güvenlik Limitleri',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.accent),
          ),
          const SizedBox(height: 8),
          const Text(
            'Hız, irtifa ve mesafe sınırları backend\'de (mission_executor) '
            'uygulanır. Uygulama yalnızca söylenen metni /voice/text konusuna gönderir.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 12),
          const Text(
            'Ses Tanıma Dili',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.accent),
          ),
          RadioGroup<String>(
            groupValue: _language,
            onChanged: (val) {
              if (val != null) setState(() => _language = val);
            },
            child: const Column(
              children: [
                RadioListTile<String>(
                  title: Text('Türkçe (tr_TR)'),
                  value: 'tr_TR',
                ),
                RadioListTile<String>(
                  title: Text('English (en_US)'),
                  value: 'en_US',
                ),
              ],
            ),
          ),
          const SizedBox(height: 30),
          ElevatedButton.icon(
            onPressed: _saveSettings,
            icon: const Icon(Icons.check),
            label: const Text('Kaydet'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ],
      ),
    );
  }
}

