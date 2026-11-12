/// BackendFeedback - `/drone/feedback` (drone_interfaces/msg/Feedback) mesajı.
///
/// Komutun ayrıştırılması, kabulü ve yürütülmesi backend'de (command_parser,
/// mission_executor) yapılır. Bu sınıf backend'in ürettiği `durum` ve `mesaj`
/// alanlarını değiştirmeden taşır; mobil uygulama içeriği yorumlamaz.
library;

class BackendFeedback {
  /// kabul | yurutuyor | tamamlandi | reddedildi | hata | bilgi
  final String durum;

  /// Backend'in insan tarafından okunabilir Türkçe mesajı
  final String mesaj;

  const BackendFeedback({required this.durum, required this.mesaj});

  /// Yalnızca görüntüleme rengi için: komut reddedildi ya da hata oluştu.
  bool get isNegative => durum == 'reddedildi' || durum == 'hata';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is BackendFeedback && other.durum == durum && other.mesaj == mesaj;

  @override
  int get hashCode => Object.hash(durum, mesaj);

  @override
  String toString() => 'BackendFeedback(durum: $durum, mesaj: $mesaj)';
}
