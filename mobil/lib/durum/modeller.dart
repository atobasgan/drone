import 'dart:convert';

enum BaglantiDurumu { kopuk, baglaniyor, bagli, hata }

enum PttDurumu { bos, dinliyor, isleniyor }

/// Konuşma nerede yazıya çevrilir?
enum SttModu {
  /// Sunucu destekliyorsa yer istasyonunda (daha doğru), yoksa telefonda.
  otomatik,

  /// Telefonun kendi tanıyıcısı; sunucuya sadece metin gider.
  telefon,

  /// Ham ses yer istasyonuna akar, orada (faster-whisper) çevrilir.
  yer,
}

enum KartDurumu { dinleniyor, isleniyor, duyuldu, komut, yurutuyor, tamamlandi, reddedildi, anlasilmadi }

class Telemetri {
  const Telemetri({
    this.hazir = false,
    this.irtifa,
    this.hiz,
    this.yaw,
    this.batarya,
    this.arm = false,
    this.havada = false,
    this.mod,
    this.enlem,
    this.boylam,
  });

  factory Telemetri.fromJson(Map<String, dynamic> j) {
    double? d(String k) => (j[k] as num?)?.toDouble();
    return Telemetri(
      hazir: j['hazir'] == true,
      irtifa: d('irtifa'),
      hiz: d('hiz'),
      yaw: d('yaw'),
      batarya: d('batarya'),
      arm: j['arm'] == true,
      havada: j['havada'] == true,
      mod: j['mod'] as String?,
      enlem: d('enlem'),
      boylam: d('boylam'),
    );
  }

  final bool hazir;
  final double? irtifa, hiz, yaw, batarya, enlem, boylam;
  final bool arm, havada;
  final String? mod;
}

/// Bir bas-konuş konuşmasının (ya da yazılı komutun) ekrandaki kartı.
class KonusmaKarti {
  KonusmaKarti({required this.id, required this.giris, DateTime? zaman})
      : zaman = zaman ?? DateTime.now();

  final int id;

  /// ses | klavye | hizli_tus
  final String giris;
  final DateTime zaman;

  KartDurumu durum = KartDurumu.dinleniyor;
  String? duyulan; // STT çıktısı (ham)
  String? normalize; // command_parser'ın normalize ettiği metin
  int? sttMs;
  String? sttKaynagi; // telefon_stt | yer_stt | klavye
  List<Map<String, dynamic>> adimlar = const [];
  String? komutKaynagi; // hizli_yol | llm | acil | onbellek
  bool kuyrugaEklendi = false;
  double? parserMs;

  /// Tuş bırakma -> komut telefona ulaştı (telefon saatiyle).
  int? toplamGecikmeMs;
  final List<String> olaylar = [];
  String? sebep;

  /// LLM'in / hızlı yolun ürettiği JSON (ekranda gösterilir).
  String get komutJson => const JsonEncoder.withIndent('  ').convert({'adimlar': adimlar});
}
