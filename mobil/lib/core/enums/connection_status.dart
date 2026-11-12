/// WebSocket / rosbridge bağlantı durumunu tanımlayan enum.
enum ConnectionStatus {
  /// Bağlantı yok
  disconnected,

  /// Bağlanılıyor...
  connecting,

  /// Bağlı ve aktif
  connected,

  /// Bağlantı hatası
  error,
}

/// ConnectionStatus için yardımcı extension
extension ConnectionStatusExtension on ConnectionStatus {
  /// Bağlantı aktif mi?
  bool get isConnected => this == ConnectionStatus.connected;

  /// Bağlantı kuruluyor mu?
  bool get isConnecting => this == ConnectionStatus.connecting;

  /// Bağlantı kesilmiş mi?
  bool get isDisconnected => this == ConnectionStatus.disconnected;

  /// Hata durumunda mı?
  bool get isError => this == ConnectionStatus.error;

  /// Türkçe durum açıklaması
  String get description {
    switch (this) {
      case ConnectionStatus.disconnected:
        return 'Bağlantı Kesildi';
      case ConnectionStatus.connecting:
        return 'Bağlanılıyor...';
      case ConnectionStatus.connected:
        return 'Bağlı';
      case ConnectionStatus.error:
        return 'Bağlantı Hatası';
    }
  }
}
