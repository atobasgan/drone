import 'package:get_it/get_it.dart';

import 'package:drone_voice_control/core/utils/connection_log.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_tts/flutter_tts.dart';

import 'package:drone_voice_control/data/datasources/rosbridge_service.dart';
import 'package:drone_voice_control/data/datasources/voice_recorder.dart';
import 'package:drone_voice_control/ses/mikrofon.dart';
import 'package:drone_voice_control/data/datasources/tts_service.dart';
import 'package:drone_voice_control/data/datasources/local_storage_service.dart';

import 'package:drone_voice_control/domain/repositories/drone_repository.dart';
import 'package:drone_voice_control/domain/repositories/settings_repository.dart';
import 'package:drone_voice_control/domain/repositories/voice_uplink_repository.dart';

import 'package:drone_voice_control/data/repositories/drone_repository_impl.dart';
import 'package:drone_voice_control/data/repositories/settings_repository_impl.dart';
import 'package:drone_voice_control/data/repositories/voice_uplink_repository_impl.dart';

import 'package:drone_voice_control/domain/usecases/get_drone_telemetry.dart';

import 'package:drone_voice_control/presentation/blocs/drone/drone_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/connection/connection_bloc.dart';

/// GetIt servis bulucu (Service Locator) — global erişim noktası
final sl = GetIt.instance;

Future<void> initializeDependencies() async {
  // ── 1. External Bağımlılıklar ──
  final sharedPreferences = await SharedPreferences.getInstance();
  sl.registerLazySingleton<SharedPreferences>(() => sharedPreferences);
  sl.registerLazySingleton<FlutterTts>(() => FlutterTts());

  // ── 2. Data Sources ──
  sl.registerLazySingleton<ConnectionLog>(() => ConnectionLog());
  sl.registerLazySingleton<RosbridgeService>(() => RosbridgeService(log: sl()));
  // Ses telefonda yazıya çevrilmez: kayıt WAV olarak backend'e gider.
  sl.registerLazySingleton<VoiceRecorder>(() => VoiceRecorder(source: Mikrofon()));
  sl.registerLazySingleton<TtsService>(() => TtsService());
  sl.registerLazySingleton<LocalStorageService>(() => LocalStorageService());

  // ── 3. Repositories ──
  sl.registerLazySingleton<DroneRepository>(
    () => DroneRepositoryImpl(rosbridgeService: sl()),
  );
  sl.registerLazySingleton<SettingsRepository>(
    () => SettingsRepositoryImpl(localStorageService: sl()),
  );
  sl.registerLazySingleton<VoiceUplinkRepository>(
    () => VoiceUplinkRepositoryImpl(rosbridgeService: sl()),
  );

  // ── 4. Use Cases ──
  sl.registerLazySingleton<GetDroneTelemetry>(
    () => GetDroneTelemetry(sl()),
  );

  // ── 5. Presentation (BLoC'lar) ──
  sl.registerFactory<DroneBloc>(
    () => DroneBloc(droneRepository: sl()),
  );
  sl.registerFactory<VoiceBloc>(
    () => VoiceBloc(
      voiceRecorder: sl(),
      voiceUplinkRepository: sl(),
    ),
  );
  sl.registerFactory<ConnectionBloc>(
    () => ConnectionBloc(droneRepository: sl()),
  );
}
