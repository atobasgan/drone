import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';

import 'package:drone_voice_control/data/datasources/rosbridge_service.dart';
import 'package:drone_voice_control/data/datasources/speech_service.dart';
import 'package:drone_voice_control/data/datasources/tts_service.dart';
import 'package:drone_voice_control/data/datasources/local_storage_service.dart';

import 'package:drone_voice_control/domain/repositories/drone_repository.dart';
import 'package:drone_voice_control/domain/repositories/voice_repository.dart';
import 'package:drone_voice_control/domain/repositories/settings_repository.dart';

import 'package:drone_voice_control/data/repositories/drone_repository_impl.dart';
import 'package:drone_voice_control/data/repositories/voice_repository_impl.dart';
import 'package:drone_voice_control/data/repositories/settings_repository_impl.dart';

import 'package:drone_voice_control/domain/usecases/process_voice_command.dart';
import 'package:drone_voice_control/domain/usecases/send_drone_command.dart';
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
  sl.registerLazySingleton<SpeechToText>(() => SpeechToText());
  sl.registerLazySingleton<FlutterTts>(() => FlutterTts());

  // ── 2. Data Sources ──
  sl.registerLazySingleton<RosbridgeService>(() => RosbridgeService());
  sl.registerLazySingleton<SpeechService>(() => SpeechService());
  sl.registerLazySingleton<TtsService>(() => TtsService());
  sl.registerLazySingleton<LocalStorageService>(() => LocalStorageService());

  // ── 3. Repositories ──
  sl.registerLazySingleton<DroneRepository>(
    () => DroneRepositoryImpl(rosbridgeService: sl()),
  );
  sl.registerLazySingleton<VoiceRepository>(
    () => VoiceRepositoryImpl(speechService: sl()),
  );
  sl.registerLazySingleton<SettingsRepository>(
    () => SettingsRepositoryImpl(localStorageService: sl()),
  );

  // ── 4. Use Cases ──
  sl.registerLazySingleton<ProcessVoiceCommand>(
    () => ProcessVoiceCommand(sl()),
  );
  sl.registerLazySingleton<SendDroneCommand>(
    () => SendDroneCommand(sl(), sl()),
  );
  sl.registerLazySingleton<GetDroneTelemetry>(
    () => GetDroneTelemetry(sl()),
  );

  // ── 5. Presentation (BLoC'lar) ──
  sl.registerFactory<DroneBloc>(
    () => DroneBloc(droneRepository: sl()),
  );
  sl.registerFactory<VoiceBloc>(
    () => VoiceBloc(
      voiceRepository: sl(),
      processVoiceCommand: sl(),
    ),
  );
  sl.registerFactory<ConnectionBloc>(
    () => ConnectionBloc(droneRepository: sl()),
  );
}
