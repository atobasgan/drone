/// Gerçek Dart istemcisi <-> gerçek Python köprüsü (deneme_sunucusu).
/// Çalıştırmak için: ./scripts/telsiz_uyum_testi.sh (TELSIZ_UYUM_URL yoksa atlanır).
library;

import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:telsiz/ayarlar/ayarlar.dart';
import 'package:telsiz/baglanti/telsiz_istemcisi.dart';
import 'package:telsiz/durum/modeller.dart';
import 'package:telsiz/durum/telsiz_kontrolcusu.dart';
import 'package:telsiz/protokol/baglanti_adresi.dart';

import 'sahteler.dart';

Future<void> bekle(bool Function() kosul, [String ne = 'koşul']) async {
  final son = DateTime.now().add(const Duration(seconds: 8));
  while (!kosul()) {
    if (DateTime.now().isAfter(son)) throw TimeoutException('$ne sağlanmadı');
    await Future<void>.delayed(const Duration(milliseconds: 20));
  }
}

void main() {
  final url = Platform.environment['TELSIZ_UYUM_URL'];

  test('telefon <-> köprü: metin, ses, red, anlaşılmayan, acil', () async {
    final mikrofon = SahteMikrofon();
    final k = TelsizKontrolcusu(
      baglanti: TelsizIstemcisi(cihazAdi: 'uyum_testi'),
      mikrofon: mikrofon,
      tanima: SahteTanima(),
      geriBildirim: SahteGeriBildirim(),
      ayarlar: const Ayarlar(sonKayitMs: 50),
    );
    await k.baglan(BaglantiAdresi.coz(url!)!);
    await bekle(() => k.bagli, 'bağlantı');
    expect(k.rol, 'operator');
    expect(k.yerSttVar, isTrue);
    expect(k.etkinMod, SttModu.yer);

    // 1) yazılı komut: gerçek hızlı yol JSON'u + güvenlik + sanal yürütme
    k.metinGonder('kalk');
    final kalk = k.kartlar.first;
    await bekle(() => kalk.durum == KartDurumu.tamamlandi, 'kalk tamamlandı');
    expect(kalk.adimlar, [
      {'komut': 'kalk'}
    ]);
    expect(kalk.komutKaynagi, 'hizli_yol');
    expect(kalk.toplamGecikmeMs, lessThan(500));
    await bekle(() => k.telemetri.havada, 'telemetri havada');

    // 2) bas-konuş: ikili PCM çerçeveleri -> köprü (sahte STT) -> parser
    await k.pttBasla();
    final sesli = k.kartlar.first;
    for (var i = 0; i < 50; i++) {
      mikrofon.besle(20, deger: 3); // gerçek zamanlı: 20 ms'de bir parça
      await Future<void>.delayed(const Duration(milliseconds: 20));
    }
    await k.pttBirak();
    await bekle(() => sesli.adimlar.isNotEmpty || sesli.sebep != null, 'sesli komut');
    expect(sesli.sebep, isNull);
    expect(sesli.duyulan, '20 metre yüksel');
    expect(sesli.sttKaynagi, 'yer_stt');
    expect(sesli.normalize, '20 m yüksel');
    expect(sesli.adimlar, [
      {'komut': 'yuksel', 'metre': 20.0}
    ]);
    await bekle(() => sesli.durum == KartDurumu.tamamlandi, 'yüksel tamamlandı');

    // 3) güvenlik katmanı reddi
    k.metinGonder('beş yüz metre yüksel');
    final red = k.kartlar.first;
    await bekle(() => red.durum == KartDurumu.reddedildi, 'red');
    expect(red.sebep, contains('sınır'));

    // 4) LLM yok, hızlı yol eşleşmedi -> anlaşılmadı
    k.metinGonder('bugün hava nasıl');
    final anlamsiz = k.kartlar.first;
    await bekle(() => anlamsiz.durum == KartDurumu.anlasilmadi, 'anlaşılmadı');

    // 5) ACİL DUR
    k.acilDur();
    await bekle(() => (k.bildirim ?? '').contains('ACİL DUR'), 'acil dur yankısı');

    await k.kopar();
  }, skip: url == null ? 'TELSIZ_UYUM_URL yok (./scripts/telsiz_uyum_testi.sh)' : false);
}
