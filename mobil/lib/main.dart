import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import 'package:drone_voice_control/core/theme/app_theme.dart';
import 'package:drone_voice_control/core/constants/app_constants.dart';
import 'package:drone_voice_control/di/injection_container.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/connection/connection_bloc.dart';
import 'package:drone_voice_control/presentation/screens/home_screen.dart';

// Telsiz modülü importları
import 'ayarlar/ayarlar.dart';
import 'baglanti/telsiz_istemcisi.dart';
import 'durum/telsiz_kontrolcusu.dart';
import 'geri_bildirim/geri_bildirimci.dart';
import 'protokol/baglanti_adresi.dart';
import 'ses/cihaz_tanima.dart';
import 'ses/mikrofon.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Eski projenin DI servislerini başlat
  await initializeDependencies();

  // Telsiz modülü ayarlarını başlat
  final telsizAyarlari = await AyarDeposu.yukle();
  final telsizKontrolcusu = TelsizKontrolcusu(
    baglanti: TelsizIstemcisi(),
    geriBildirim: CihazGeriBildirimci(sesAcik: telsizAyarlari.sesliYanit, titresimAcik: telsizAyarlari.titresim),
    tanima: SistemTanima(),
    mikrofon: Mikrofon(),
    ayarlar: telsizAyarlari,
  );

  await WakelockPlus.enable();

  final son = BaglantiAdresi.coz(telsizAyarlari.sunucuAdresi, token: telsizAyarlari.token);
  if (son != null && son.token.isNotEmpty) {
    telsizKontrolcusu.baglan(son);
  }

  runApp(DroneVoiceControlApp(telsizKontrolcusu: telsizKontrolcusu));
}

class DroneVoiceControlApp extends StatelessWidget {
  const DroneVoiceControlApp({super.key, required this.telsizKontrolcusu});

  final TelsizKontrolcusu telsizKontrolcusu;

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<DroneBloc>(
          create: (_) => sl<DroneBloc>(),
        ),
        BlocProvider<VoiceBloc>(
          create: (_) => sl<VoiceBloc>(),
        ),
        BlocProvider<ConnectionBloc>(
          create: (_) => sl<ConnectionBloc>(),
        ),
      ],
      child: MaterialApp(
        title: AppConstants.appName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.dark,
        home: HomeScreen(telsizKontrolcusu: telsizKontrolcusu),
      ),
    );
  }
}
