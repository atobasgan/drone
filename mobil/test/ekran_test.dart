import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:telsiz/ayarlar/ayarlar.dart';
import 'package:telsiz/durum/telsiz_kontrolcusu.dart';
import 'package:telsiz/ekranlar/telsiz_ekrani.dart';

import 'sahteler.dart';

void main() {
  testWidgets('telsiz ekranı: bas-konuş, kart, ACİL DUR', (tester) async {
    final b = SahteBaglanti();
    final k = TelsizKontrolcusu(
      baglanti: b,
      mikrofon: SahteMikrofon(),
      tanima: SahteTanima(),
      geriBildirim: SahteGeriBildirim(),
      ayarlar: const Ayarlar(sonKayitMs: 0),
      enKisaBasma: Duration.zero,
    );
    b.gelsin({'tip': 'hos_geldin', 'rol': 'operator', 'yer_stt': false});
    await tester.pumpWidget(MaterialApp(home: TelsizEkrani(kontrolcu: k)));
    expect(find.text('BAS KONUŞ'), findsOneWidget);
    expect(find.text('OPERATÖR'), findsOneWidget);

    final gesture = await tester.startGesture(tester.getCenter(find.text('BAS KONUŞ')));
    await tester.pump();
    expect(find.text('KONUŞ'), findsOneWidget);
    await gesture.up();
    await tester.pumpAndSettle();
    final id = b.giden.single['id'];
    b.gelsin({
      'tip': 'komut',
      'id': id,
      'kaynak': 'llm',
      'metin': '20 m yüksel',
      'adimlar': [
        {'komut': 'yuksel', 'metre': 20}
      ],
    });
    await tester.pump();
    expect(find.text('20 m yüksel'), findsWidgets);
    expect(find.text('LLM'), findsOneWidget);

    await tester.tap(find.text('ACİL DUR'));
    expect(b.giden.last['tip'], 'acil_dur');

    await tester.tap(find.text('eve dön'));
    expect(b.giden.last, containsPair('metin', 'eve dön'));
  });
}
