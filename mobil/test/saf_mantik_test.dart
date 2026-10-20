import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:telsiz/durum/komut_aciklama.dart';
import 'package:telsiz/protokol/baglanti_adresi.dart';
import 'package:telsiz/protokol/mesajlar.dart';
import 'package:telsiz/ses/halka_tampon.dart';
import 'package:telsiz/ses/pcm_parcalayici.dart';
import 'package:telsiz/ses/seviye.dart';

void main() {
  group('protokol', () {
    test('ses parçası başlığı little-endian [id][sıra] + PCM', () {
      final c = sesParcasi(0x01020304, 7, Uint8List.fromList([9, 8]));
      expect(c, [4, 3, 2, 1, 7, 0, 0, 0, 9, 8]);
    });
    test('20 ms = 640 bayt, ms->bayt çift', () {
      expect(parcaBayt, 640);
      expect(msToBayt(300), 9600);
      expect(msToBayt(1) % 2, 0);
    });
    test('json yaz / çöz', () {
      expect(jsonYaz('metin', {'id': 1, 'metin': 'yüksel'}), '{"tip":"metin","id":1,"metin":"yüksel"}');
      expect(jsonCoz('{"tip":"pong","t":5}'), {'tip': 'pong', 't': 5});
      expect(jsonCoz('bozuk'), isNull);
      expect(jsonCoz('{"x":1}'), isNull);
      expect(jsonCoz(Uint8List(3)), isNull);
    });
  });

  group('bağlantı adresi', () {
    test('QR adresi', () {
      final a = BaglantiAdresi.coz('ws://192.168.1.5:8765/telsiz?token=ABC')!;
      expect(a.uri.toString(), 'ws://192.168.1.5:8765/telsiz');
      expect(a.token, 'ABC');
      expect(a.tamMetin, 'ws://192.168.1.5:8765/telsiz?token=ABC');
    });
    test('kısa yazımlar ve ayrı token', () {
      expect(BaglantiAdresi.coz('10.0.0.2')!.uri.toString(), 'ws://10.0.0.2:8765/telsiz');
      expect(BaglantiAdresi.coz('10.0.0.2:9000', token: ' T ')!.token, 'T');
      expect(BaglantiAdresi.coz('ws://h:1/telsiz?token=A', token: 'B')!.token, 'B');
    });
    test('geçersiz', () {
      expect(BaglantiAdresi.coz(''), isNull);
      expect(BaglantiAdresi.coz('http://x'), isNull);
      expect(BaglantiAdresi.coz('ws://'), isNull);
    });
  });

  group('halka tampon (ön kayıt)', () {
    test('son N baytı sırayla tutar', () {
      final t = HalkaTampon(4)
        ..ekle(Uint8List.fromList([1, 2, 3]))
        ..ekle(Uint8List.fromList([4, 5]));
      expect(t.al(), [2, 3, 4, 5]);
      t.ekle(Uint8List.fromList([6, 7, 8, 9, 10]));
      expect(t.al(), [7, 8, 9, 10]);
      t.temizle();
      expect(t.al(), isEmpty);
    });
    test('dolmadan', () {
      final t = HalkaTampon(10)..ekle(Uint8List.fromList([1, 2]));
      expect(t.al(), [1, 2]);
    });
  });

  group('PCM parçalayıcı', () {
    test('640 baytlık parçalar + kalan', () {
      final p = PcmParcalayici();
      expect(p.ekle(Uint8List(500)), isEmpty);
      final parcalar = p.ekle(Uint8List(1000)); // 1500 bayt -> 2 parça, 220 kalan
      expect(parcalar.map((e) => e.length), [640, 640]);
      expect(p.bosalt()!.length, 220);
      expect(p.bosalt(), isNull);
    });
    test('tek bayt kalan kırpılır', () {
      final p = PcmParcalayici()..ekle(Uint8List(3));
      expect(p.bosalt()!.length, 2);
    });
  });

  test('ses seviyesi', () {
    expect(sesSeviyesi(Uint8List(640)), 0);
    final yuksek = Uint8List(640);
    final v = ByteData.sublistView(yuksek);
    for (var i = 0; i < 320; i++) {
      v.setInt16(i * 2, i.isEven ? 30000 : -30000, Endian.little);
    }
    expect(sesSeviyesi(yuksek), greaterThan(0.9));
  });

  group('komut açıklaması (LLM şeması)', () {
    test('adımlar', () {
      expect(adimAciklamasi({'komut': 'yuksel', 'metre': 20}), '20 m yüksel');
      expect(adimAciklamasi({'komut': 'git_yon', 'yon': 'kuzey', 'metre': 50}), 'kuzeye 50 m git');
      expect(adimAciklamasi({'komut': 'don', 'yon': 'sag', 'derece': 90}), 'sağa 90° dön');
      expect(adimAciklamasi({'komut': 'kalk', 'irtifa_m': 10}), "10 m'ye kalk");
      expect(adimAciklamasi({'komut': 'alcal', 'metre': 1.5}), '1.5 m alçal');
      expect(
          adimlarAciklamasi([
            {'komut': 'yuksel', 'metre': 20},
            {'komut': 'eve_don'},
          ]),
          '20 m yüksel → eve dön');
      expect(kaynakEtiketi('hizli_yol'), 'HIZLI YOL');
      expect(kaynakEtiketi('llm'), 'LLM');
    });
  });
}
