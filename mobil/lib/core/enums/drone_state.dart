/// Drone'un uçuş durumlarını tanımlayan enum.
/// Durum makinesi: grounded → takingOff → hovering ↔ flying → landing → grounded
enum DroneFlightState {
  /// Yerde, motorlar kapalı
  grounded,

  /// Kalkış yapıyor
  takingOff,

  /// Havada sabit duruyor (hover)
  hovering,

  /// Aktif uçuş halinde
  flying,

  /// İniş yapıyor
  landing,

  /// Acil durum — tüm motorlar durduruldu
  emergency,
}

/// DroneFlightState için yardımcı extension
extension DroneFlightStateExtension on DroneFlightState {
  /// Drone havada mı? (kalkış, hover, uçuş veya iniş)
  bool get isAirborne =>
      this == DroneFlightState.takingOff ||
      this == DroneFlightState.hovering ||
      this == DroneFlightState.flying ||
      this == DroneFlightState.landing;

  /// Drone komut kabul edebilir durumda mı?
  bool get canAcceptCommands =>
      this == DroneFlightState.hovering || this == DroneFlightState.flying;

  /// Drone kalkış yapabilir mi?
  bool get canTakeOff => this == DroneFlightState.grounded;

  /// Drone iniş yapabilir mi?
  bool get canLand => isAirborne && this != DroneFlightState.landing;

  /// Türkçe durum açıklaması
  String get description {
    switch (this) {
      case DroneFlightState.grounded:
        return 'Yerde';
      case DroneFlightState.takingOff:
        return 'Kalkış Yapılıyor';
      case DroneFlightState.hovering:
        return 'Havada Sabit';
      case DroneFlightState.flying:
        return 'Uçuş Halinde';
      case DroneFlightState.landing:
        return 'İniş Yapılıyor';
      case DroneFlightState.emergency:
        return 'ACİL DURUM';
    }
  }
}
