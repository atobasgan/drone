import 'package:flutter/material.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import 'app.dart';
import 'ayarlar/ayarlar.dart';
import 'baglanti/telsiz_istemcisi.dart';
import 'durum/telsiz_kontrolcusu.dart';
import 'geri_bildirim/geri_bildirimci.dart';
import 'protokol/baglanti_adresi.dart';
import 'ses/cihaz_tanima.dart';
import 'ses/mikrofon.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final ayarlar = await AyarDeposu.yukle();
  final kontrolcu = TelsizKontrolcusu(
    baglanti: TelsizIstemcisi(),
    mikrofon: Mikrofon(),
    tanima: SistemTanima(),
    geriBildirim: CihazGeriBildirimci(sesAcik: ayarlar.sesliYanit, titresimAcik: ayarlar.titresim),
    ayarlar: ayarlar,
  );
  // Telsiz kullanılırken ekran kararmasın.
  await WakelockPlus.enable();
  runApp(TelsizUygulamasi(kontrolcu: kontrolcu));

  // Son kullanılan yer istasyonuna kendiliğinden bağlan.
  final son = BaglantiAdresi.coz(ayarlar.sunucuAdresi, token: ayarlar.token);
  if (son != null && son.token.isNotEmpty) await kontrolcu.baglan(son);
}
