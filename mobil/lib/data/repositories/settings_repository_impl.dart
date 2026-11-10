import 'package:drone_voice_control/data/datasources/local_storage_service.dart';
import 'package:drone_voice_control/domain/repositories/settings_repository.dart';

class SettingsRepositoryImpl implements SettingsRepository {
  final LocalStorageService localStorageService;

  SettingsRepositoryImpl({required this.localStorageService});

  @override
  Future<String> getRosbridgeHost() async {
    return await localStorageService.getString(
      LocalStorageService.keyRosbridgeHost,
      defaultValue: LocalStorageService.defaultHost,
    );
  }

  @override
  Future<void> setRosbridgeHost(String host) async {
    await localStorageService.setString(LocalStorageService.keyRosbridgeHost, host);
  }

  @override
  Future<int> getRosbridgePort() async {
    return await localStorageService.getInt(
      LocalStorageService.keyRosbridgePort,
      defaultValue: LocalStorageService.defaultPort,
    );
  }

  @override
  Future<void> setRosbridgePort(int port) async {
    await localStorageService.setInt(LocalStorageService.keyRosbridgePort, port);
  }

  @override
  Future<String> getLanguage() async {
    return await localStorageService.getString(
      LocalStorageService.keyLanguage,
      defaultValue: LocalStorageService.defaultLanguage,
    );
  }

  @override
  Future<void> setLanguage(String language) async {
    await localStorageService.setString(LocalStorageService.keyLanguage, language);
  }

  @override
  Future<double> getMaxSpeed() async {
    return await localStorageService.getDouble(
      LocalStorageService.keyMaxSpeed,
      defaultValue: LocalStorageService.defaultMaxSpeed,
    );
  }

  @override
  Future<void> setMaxSpeed(double speed) async {
    await localStorageService.setDouble(LocalStorageService.keyMaxSpeed, speed);
  }

  @override
  Future<SafetyLimits> getSafetyLimits() async {
    final maxXY = await localStorageService.getDouble(
      LocalStorageService.keyMaxLinearXY,
      defaultValue: 3.0,
    );
    final maxZ = await localStorageService.getDouble(
      LocalStorageService.keyMaxLinearZ,
      defaultValue: 2.5,
    );
    final maxAngZ = await localStorageService.getDouble(
      LocalStorageService.keyMaxAngularZ,
      defaultValue: 2.0,
    );
    final step = await localStorageService.getDouble(
      LocalStorageService.keySpeedStep,
      defaultValue: 0.5,
    );

    return SafetyLimits(
      maxLinearXY: maxXY,
      maxLinearZ: maxZ,
      maxAngularZ: maxAngZ,
      speedStep: step,
    );
  }

  @override
  Future<void> setSafetyLimits(SafetyLimits limits) async {
    await localStorageService.setDouble(
      LocalStorageService.keyMaxLinearXY,
      limits.maxLinearXY,
    );
    await localStorageService.setDouble(
      LocalStorageService.keyMaxLinearZ,
      limits.maxLinearZ,
    );
    await localStorageService.setDouble(
      LocalStorageService.keyMaxAngularZ,
      limits.maxAngularZ,
    );
    await localStorageService.setDouble(
      LocalStorageService.keySpeedStep,
      limits.speedStep,
    );
  }
}

