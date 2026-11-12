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
}
