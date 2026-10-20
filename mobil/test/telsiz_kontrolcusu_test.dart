import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:telsiz/ayarlar/ayarlar.dart';
import 'package:telsiz/durum/modeller.dart';
import 'package:telsiz/durum/telsiz_kontrolcusu.dart';
import 'package:telsiz/geri_bildirim/geri_bildirimci.dart';

import 'sahteler.dart';

typedef Ortam = ({
  TelsizKontrolcusu k,
  SahteBaglanti b,
  SahteMikrofon m,
  SahteTanima t,
  SahteGeriBildirim g,
});

Ortam kur({bool yerStt = true, Ayarlar ayarlar = const Ayarlar(sonKayitMs: 0), String rol = 'operator'}) {
  final b = SahteBaglanti();
  final m = SahteMikrofon();
  final t = SahteTanima();
  final g = SahteGeriBildirim();
  final k = TelsizKontrolcusu(
      baglanti: b, mikrofon: m, tanima: t, geriBildirim: g, ayarlar: ayarlar, enKisaBasma: Duration.zero);
  b.gelsin({'tip': 'hos_geldin', 'rol': rol, 'yer_stt': yerStt, 'stt_motoru': 'faster_whisper'});
  return (k: k, b: b, m: m, t: t, g: g);
}

({int id, int sira, int uzunluk, int ilkBayt}) coz(Uint8List c) {
  final v = ByteData.sublistView(c);
  return (id: v.getUint32(0, Endian.little), sira: v.getUint32(4, Endian.little), uzunluk: c.length - 8, ilkBayt: c[8]);
}

void main() {
  test('yer STT: ön kayıt + canlı ses + ptt_bitti', () async {
    final o = kur();
    await pumpEventQueue();
    expect(o.k.etkinMod, SttModu.yer);
    expect(o.m.acik, isTrue, reason: 'ön kayıt için mikrofon açık');
    o.m.besle(1000, deger: 7); // tuştan önce 1 sn: sadece son 300 ms tutulmalı
    expect(o.b.ses, isEmpty, reason: 'tuşa basılmadan ses telefondan çıkmaz');

    await o.k.pttBasla();
    expect(o.b.tipler, ['ptt_basla']);
    final id = o.b.giden.first['id'] as int;
    o.m.besle(1000, deger: 9);
    await o.k.pttBirak();

    final parcalar = o.b.ses.map(coz).toList();
    expect(parcalar.every((p) => p.id == id), isTrue);
    expect([for (final p in parcalar) p.sira], List.generate(parcalar.length, (i) => i));
    final onKayitBayt = parcalar.where((p) => p.ilkBayt == 7).fold(0, (s, p) => s + p.uzunluk);
    expect(onKayitBayt, 9600, reason: '300 ms ön kayıt');
    final toplam = parcalar.fold(0, (s, p) => s + p.uzunluk);
    expect(toplam, 9600 + 32000);
    expect(o.b.giden.last, {'tip': 'ptt_bitti', 'id': id, 'parca_sayisi': parcalar.length});
    expect(o.k.kartlar.single.durum, KartDurumu.isleniyor);
    expect(o.k.ptt, PttDurumu.bos);
    expect(o.g.titresimler.take(2), [Titresim.basla, Titresim.birak]);
  });

  test('yer STT, ön kayıt kapalı: mikrofon tuşla açılır/kapanır', () async {
    final o = kur(ayarlar: const Ayarlar(sonKayitMs: 0, onKayit: false));
    await pumpEventQueue();
    expect(o.m.acik, isFalse);
    await o.k.pttBasla();
    expect(o.m.acik, isTrue);
    o.m.besle(500);
    await o.k.pttBirak();
    expect(o.m.acik, isFalse);
    expect(o.b.tipler.last, 'ptt_bitti');
  });

  test('telefon STT: metin gönderilir, ses gönderilmez', () async {
    final o = kur(yerStt: false);
    await pumpEventQueue();
    expect(o.k.etkinMod, SttModu.telefon);
    expect(o.m.acik, isFalse);
    await o.k.pttBasla();
    expect(o.t.dinliyor, isTrue);
    expect(o.t.sonDil, 'tr_TR');
    expect(o.k.kismiMetin, '20 metre');
    await o.k.pttBirak();
    final m = o.b.giden.single;
    expect(m['tip'], 'metin');
    expect(m['metin'], '20 metre yüksel');
    expect(m['kaynak'], 'telefon_stt');
    expect(o.b.ses, isEmpty);
    expect(o.k.kartlar.single.duyulan, '20 metre yüksel');
  });

  test('sunucudan gelen komut ve geri bildirim kartı günceller', () async {
    final o = kur(yerStt: false);
    await o.k.pttBasla();
    await o.k.pttBirak();
    final id = o.b.giden.single['id'] as int;
    o.b.gelsin({'tip': 'duyuldu', 'id': id, 'metin': '20 metre yüksel', 'kaynak': 'telefon_stt'});
    o.b.gelsin({
      'tip': 'komut',
      'id': id,
      'metin': '20 m yüksel',
      'kaynak': 'hizli_yol',
      'kuyruga_ekle': false,
      'adimlar': [
        {'komut': 'yuksel', 'metre': 20}
      ],
      'parser_ms': 0.1,
    });
    final kart = o.k.kartlar.single;
    expect(kart.durum, KartDurumu.komut);
    expect(kart.komutKaynagi, 'hizli_yol');
    expect(kart.normalize, '20 m yüksel');
    expect(kart.toplamGecikmeMs, isNotNull);
    expect(kart.komutJson, contains('"komut": "yuksel"'));
    expect(TelsizKontrolcusu.kartBasligi(kart), '20 m yüksel');

    o.b.gelsin({'tip': 'geri_bildirim', 'id': id, 'durum': 'yurutuyor', 'mesaj': '20 metre yükseliyorum'});
    expect(kart.durum, KartDurumu.yurutuyor);
    expect(o.g.soylenen, ['20 metre yükseliyorum']);
    o.b.gelsin({'tip': 'geri_bildirim', 'id': id, 'durum': 'tamamlandi', 'mesaj': 'yuksel tamamlandı'});
    expect(kart.durum, KartDurumu.tamamlandi);
  });

  test('güvenlik reddi ve anlaşılmayan cümle', () async {
    final o = kur(yerStt: false);
    o.k.metinGonder('5000 metre yüksel');
    final id1 = o.b.giden.last['id'] as int;
    o.b.gelsin({'tip': 'geri_bildirim', 'id': id1, 'durum': 'reddedildi', 'mesaj': 'hedef irtifa 5010 m, sınır 600 m'});
    expect(o.k.kartlar.first.durum, KartDurumu.reddedildi);
    expect(o.k.kartlar.first.sebep, contains('600'));
    expect(o.g.titresimler.last, Titresim.red);

    o.k.metinGonder('saat kaç');
    final id2 = o.b.giden.last['id'] as int;
    o.b.gelsin({'tip': 'anlasilmadi', 'id': id2, 'sebep': 'anlamadım: "saat kaç"'});
    expect(o.k.kartlar.first.durum, KartDurumu.anlasilmadi);
    expect(o.g.soylenen.last, 'Anlamadım');
  });

  test('çok kısa basış iptal edilir', () async {
    final o = kur();
    final k = TelsizKontrolcusu(
        baglanti: o.b, mikrofon: o.m, tanima: o.t, geriBildirim: o.g, enKisaBasma: const Duration(seconds: 5));
    o.b.gelsin({'tip': 'hos_geldin', 'rol': 'operator', 'yer_stt': true});
    await k.pttBasla();
    await k.pttBirak();
    expect(o.b.tipler.where((t) => t.startsWith('ptt')), ['ptt_basla', 'ptt_iptal']);
    expect(k.kartlar, isEmpty);
  });

  test('izleyici konuşamaz ama ACİL DUR verebilir', () async {
    final o = kur(rol: 'izleyici');
    expect(o.k.komutVerebilir, isFalse);
    await o.k.pttBasla();
    o.k.metinGonder('kalk');
    expect(o.b.giden, isEmpty);
    o.k.acilDur();
    expect(o.b.tipler, ['acil_dur']);
    expect(o.g.titresimler.last, Titresim.acil);
  });

  test('bağlantı yokken ACİL DUR kullanıcıyı uyarır', () {
    final o = kur();
    o.b.koptu();
    o.k.acilDur();
    expect(o.b.giden, isEmpty);
    expect(o.k.bildirim, contains('gönderilemedi'));
  });

  test('konuşurken bağlantı koparsa PTT iptal olur', () async {
    final o = kur();
    await o.k.pttBasla();
    o.b.koptu();
    await pumpEventQueue();
    expect(o.k.ptt, PttDurumu.bos);
    expect(o.k.kartlar, isEmpty);
  });

  test('telsiz koptu / acil dur bildirimi ve izleyici için uzak kart', () {
    final o = kur(rol: 'izleyici');
    o.b.gelsin({'tip': 'geri_bildirim', 'id': null, 'durum': 'telsiz_koptu', 'mesaj': 'operatörden 3 sn sinyal yok'});
    expect(o.k.bildirim, contains('3 sn'));
    expect(o.g.soylenen.last, 'Telsiz bağlantısı koptu');
    o.b.gelsin({'tip': 'duyuldu', 'id': 77, 'metin': 'kalk', 'kaynak': 'yer_stt', 'stt_ms': 210});
    expect(o.k.kartlar.single.giris, 'uzak');
    expect(o.k.kartlar.single.sttMs, 210);
  });

  test('telemetri', () {
    final o = kur();
    o.b.gelsin({'tip': 'telemetri', 'hazir': true, 'irtifa': 20.3, 'batarya': 0.86, 'arm': true, 'havada': true, 'mod': 'OFFBOARD'});
    expect(o.k.telemetri.irtifa, 20.3);
    expect(o.k.telemetri.mod, 'OFFBOARD');
  });

  test('hızlı tuş metin olarak gider (telefon komutu yorumlamaz)', () {
    final o = kur();
    o.k.metinGonder('eve dön', giris: 'hizli_tus');
    expect(o.b.giden.single, containsPair('metin', 'eve dön'));
    expect(o.b.giden.single, containsPair('kaynak', 'hizli_tus'));
  });

  test('komut, duyuldu mesajından önce gelirse durum geri çekilmez', () async {
    final o = kur(yerStt: false);
    o.k.metinGonder('kalk');
    final id = o.b.giden.last['id'] as int;
    o.b.gelsin({'tip': 'komut', 'id': id, 'kaynak': 'hizli_yol', 'adimlar': [{'komut': 'kalk'}]});
    o.b.gelsin({'tip': 'duyuldu', 'id': id, 'metin': 'kalk', 'kaynak': 'klavye'});
    expect(o.k.kartlar.first.durum, KartDurumu.komut);
  });
}
