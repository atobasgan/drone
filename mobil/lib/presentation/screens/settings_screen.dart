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
  double _maxSpeed = 3.0;
  double _speedStep = 0.5;
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
    final speed = await _settingsRepo.getMaxSpeed();
    final limits = await _settingsRepo.getSafetyLimits();
    final lang = await _settingsRepo.getLanguage();

    setState(() {
      _hostController.text = host;
      _portController.text = port.toString();
      _maxSpeed = speed;
      _speedStep = limits.speedStep;
      _language = lang;
    });
  }

  Future<void> _saveSettings() async {
    await _settingsRepo.setRosbridgeHost(_hostController.text.trim());
    final port = int.tryParse(_portController.text.trim()) ?? 9090;
    await _settingsRepo.setRosbridgePort(port);
    await _settingsRepo.setMaxSpeed(_maxSpeed);
    await _settingsRepo.setLanguage(_language);
    await _settingsRepo.setSafetyLimits(
      SafetyLimits(
        maxLinearXY: _maxSpeed,
        maxLinearZ: 2.5,
        maxAngularZ: 2.0,
        speedStep: _speedStep,
      ),
    );

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
            'Hız ve Güvenlik Limitleri (sim-drone uyumlu)',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.accent),
          ),
          const SizedBox(height: 12),
          Text('Maksimum Hız: ${_maxSpeed.toStringAsFixed(1)} m/s'),
          Slider(
            value: _maxSpeed,
            min: 1.0,
            max: 5.0,
            divisions: 8,
            label: '${_maxSpeed.toStringAsFixed(1)} m/s',
            onChanged: (val) => setState(() => _maxSpeed = val),
          ),
          const SizedBox(height: 12),
          Text('Hız Artış Adımı: ${_speedStep.toStringAsFixed(1)} m/s'),
          Slider(
            value: _speedStep,
            min: 0.2,
            max: 1.0,
            divisions: 8,
            label: '${_speedStep.toStringAsFixed(1)} m/s',
            onChanged: (val) => setState(() => _speedStep = val),
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

