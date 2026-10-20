import 'package:shared_preferences/shared_preferences.dart';

import '../durum/modeller.dart';

/// Kullanıcı ayarları (telefonda saklanır).
class Ayarlar {
  const Ayarlar({
    this.sunucuAdresi = '',
    this.token = '',
    this.izleyici = false,
    this.sttModu = SttModu.otomatik,
    this.onKayit = true,
    this.sonKayitMs = 150,
    this.sesliYanit = true,
    this.titresim = true,
    this.cevrimdisiTanima = false,
    this.gurultuBastirma = false,
    this.dil = 'tr_TR',
  });

  final String sunucuAdresi;
  final String token;

  /// Sadece izle (komut veremez, ACİL DUR verebilir).
  final bool izleyici;
  final SttModu sttModu;

  /// Yer STT modunda mikrofonu açık tutup tuştan önceki 300 ms'yi de gönder.
  final bool onKayit;

  /// Tuş bırakıldıktan sonra son hece kesilmesin diye kayda devam süresi.
  final int sonKayitMs;
  final bool sesliYanit;
  final bool titresim;

  /// Telefonda tanımada internetsiz (cihaz üstü) tanıma iste.
  final bool cevrimdisiTanima;
  final bool gurultuBastirma;
  final String dil;

  Ayarlar copyWith({
    String? sunucuAdresi,
    String? token,
    bool? izleyici,
    SttModu? sttModu,
    bool? onKayit,
    int? sonKayitMs,
    bool? sesliYanit,
    bool? titresim,
    bool? cevrimdisiTanima,
    bool? gurultuBastirma,
  }) =>
      Ayarlar(
        sunucuAdresi: sunucuAdresi ?? this.sunucuAdresi,
        token: token ?? this.token,
        izleyici: izleyici ?? this.izleyici,
        sttModu: sttModu ?? this.sttModu,
        onKayit: onKayit ?? this.onKayit,
        sonKayitMs: sonKayitMs ?? this.sonKayitMs,
        sesliYanit: sesliYanit ?? this.sesliYanit,
        titresim: titresim ?? this.titresim,
        cevrimdisiTanima: cevrimdisiTanima ?? this.cevrimdisiTanima,
        gurultuBastirma: gurultuBastirma ?? this.gurultuBastirma,
        dil: dil,
      );
}

class AyarDeposu {
  static Future<Ayarlar> yukle() async {
    final p = await SharedPreferences.getInstance();
    return Ayarlar(
      sunucuAdresi: p.getString('sunucuAdresi') ?? '',
      token: p.getString('token') ?? '',
      izleyici: p.getBool('izleyici') ?? false,
      sttModu: SttModu.values.asNameMap()[p.getString('sttModu')] ?? SttModu.otomatik,
      onKayit: p.getBool('onKayit') ?? true,
      sonKayitMs: p.getInt('sonKayitMs') ?? 150,
      sesliYanit: p.getBool('sesliYanit') ?? true,
      titresim: p.getBool('titresim') ?? true,
      cevrimdisiTanima: p.getBool('cevrimdisiTanima') ?? false,
      gurultuBastirma: p.getBool('gurultuBastirma') ?? false,
    );
  }

  static Future<void> kaydet(Ayarlar a) async {
    final p = await SharedPreferences.getInstance();
    await p.setString('sunucuAdresi', a.sunucuAdresi);
    await p.setString('token', a.token);
    await p.setBool('izleyici', a.izleyici);
    await p.setString('sttModu', a.sttModu.name);
    await p.setBool('onKayit', a.onKayit);
    await p.setInt('sonKayitMs', a.sonKayitMs);
    await p.setBool('sesliYanit', a.sesliYanit);
    await p.setBool('titresim', a.titresim);
    await p.setBool('cevrimdisiTanima', a.cevrimdisiTanima);
    await p.setBool('gurultuBastirma', a.gurultuBastirma);
  }
}
