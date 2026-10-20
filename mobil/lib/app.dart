import 'package:flutter/material.dart';

import 'durum/modeller.dart';
import 'durum/telsiz_kontrolcusu.dart';
import 'ekranlar/baglan_ekrani.dart';
import 'ekranlar/telsiz_ekrani.dart';

class TelsizUygulamasi extends StatelessWidget {
  const TelsizUygulamasi({super.key, required this.kontrolcu});

  final TelsizKontrolcusu kontrolcu;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Drone Telsizi',
      debugShowCheckedModeBanner: false,
      // Sahada güneş altında okunaklı: koyu, yüksek kontrastlı tema.
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF00B0FF), brightness: Brightness.dark),
      ),
      home: ListenableBuilder(
        listenable: kontrolcu,
        builder: (context, _) {
          // Bir kez bağlandıktan sonra kopmalarda telsiz ekranı kalır (yeniden bağlanır).
          final telsiz = kontrolcu.bagli ||
              (kontrolcu.baglantiDurumu != BaglantiDurumu.kopuk && kontrolcu.kartlar.isNotEmpty);
          return telsiz ? TelsizEkrani(kontrolcu: kontrolcu) : BaglanEkrani(kontrolcu: kontrolcu);
        },
      ),
    );
  }
}
