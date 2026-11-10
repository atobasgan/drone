/// RosbridgeService - Rosbridge WebSocket üzerinden ROS 2 iletişim servisi.
///
/// Gazebo Sim drone ile rosbridge_websocket aracılığıyla iletişim kurar.
/// Rosbridge v2.0 protokolü JSON mesajları kullanılır.
///
/// Desteklenen topic'ler:
/// - `/drone/cmd_vel` (geometry_msgs/Twist) → komut yayınlama
/// - `/drone/odometry` (nav_msgs/Odometry) → konum ve hız aboneliği
/// - `/drone/imu` (sensor_msgs/Imu) → ivmeölçer ve jiroskop aboneliği
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Rosbridge WebSocket bağlantı durumlarını tanımlayan enum.
enum RosbridgeConnectionState {
  /// Bağlantı yok
  disconnected,

  /// Bağlantı kuruluyor
  connecting,

  /// Bağlantı kuruldu
  connected,

  /// Bağlantı hatası
  error,

  /// Yeniden bağlanılıyor
  reconnecting,
}

/// Rosbridge WebSocket servisi.
///
/// ROS 2 düğümleriyle rosbridge_websocket üzerinden iletişim sağlar.
/// Topic'lere abone olma, mesaj yayınlama ve bağlantı yönetimi
/// işlemlerini gerçekleştirir.
class RosbridgeService {
  /// WebSocket bağlantısı
  WebSocket? _webSocket;

  /// Bağlantı durumu stream controller
  final _connectionStateController =
      StreamController<RosbridgeConnectionState>.broadcast();

  /// Gelen mesajlar için topic bazlı stream controller'lar
  final Map<String, StreamController<Map<String, dynamic>>>
      _topicControllers = {};

  /// Mevcut bağlantı durumu
  RosbridgeConnectionState _currentState =
      RosbridgeConnectionState.disconnected;

  /// Yeniden bağlanma zamanlayıcısı
  Timer? _reconnectTimer;

  /// Heartbeat (canlılık kontrolü) zamanlayıcısı
  Timer? _heartbeatTimer;

  /// Rosbridge sunucu adresi
  String? _host;

  /// Rosbridge sunucu portu
  int? _port;

  /// Yeniden bağlanma denemesi sayısı
  int _reconnectAttempts = 0;

  /// Maksimum yeniden bağlanma denemesi
  static const int _maxReconnectAttempts = 10;

  /// Yeniden bağlanma bekleme süresi (saniye)
  static const int _reconnectDelaySec = 3;

  /// Heartbeat gönderim aralığı (saniye)
  static const int _heartbeatIntervalSec = 10;

  /// Bağlantı durumu akışı
  Stream<RosbridgeConnectionState> get connectionStateStream =>
      _connectionStateController.stream;

  /// Mevcut bağlantı durumu
  RosbridgeConnectionState get currentState => _currentState;

  /// Bağlı olup olmadığı
  bool get isConnected => _currentState == RosbridgeConnectionState.connected;

  /// Sunucu host adresi
  String? get host => _host;

  /// Sunucu port numarası
  int? get port => _port;

  /// Rosbridge sunucusuna WebSocket bağlantısı kurar.
  ///
  /// [host]: Rosbridge sunucu adresi (ör. "192.168.1.100")
  /// [port]: Rosbridge sunucu portu (varsayılan: 9090)
  Future<bool> connect(String host, int port) async {
    _host = host;
    _port = port;
    _reconnectAttempts = 0;

    return _establishConnection();
  }

  /// WebSocket bağlantısını kurar (iç kullanım).
  Future<bool> _establishConnection() async {
    if (_host == null || _port == null) return false;

    _updateState(RosbridgeConnectionState.connecting);

    try {
      final uri = 'ws://$_host:$_port';
      _webSocket = await WebSocket.connect(uri).timeout(
        const Duration(seconds: 10),
      );

      _updateState(RosbridgeConnectionState.connected);
      _reconnectAttempts = 0;

      // Gelen mesajları dinle
      _webSocket!.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
        cancelOnError: false,
      );

      // Heartbeat başlat
      _startHeartbeat();

      return true;
    } on SocketException catch (e) {
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
      // SocketException: Bağlantı hatası
      _log('Bağlantı hatası: $e');
      return false;
    } on TimeoutException {
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
      _log('Bağlantı zaman aşımı');
      return false;
    } catch (e) {
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
      _log('Beklenmeyen bağlantı hatası: $e');
      return false;
    }
  }

  /// Bağlantıyı kapatır ve kaynakları temizler.
  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;

    // Abonelikleri iptal et
    for (final controller in _topicControllers.values) {
      await controller.close();
    }
    _topicControllers.clear();

    // WebSocket'i kapat
    await _webSocket?.close(WebSocketStatus.normalClosure, 'Kullanıcı kapatma');
    _webSocket = null;

    _updateState(RosbridgeConnectionState.disconnected);
  }

  /// Bir ROS topic'ine mesaj yayınlar (advertise + publish).
  ///
  /// [topic]: Hedef topic adı (ör. "/drone/cmd_vel")
  /// [type]: Mesaj tipi (ör. "geometry_msgs/Twist")
  /// [msg]: Yayınlanacak mesaj içeriği
  void publish(String topic, String type, Map<String, dynamic> msg) {
    if (!isConnected || _webSocket == null) {
      _log('Yayınlama başarısız: bağlantı yok');
      return;
    }

    final publishMsg = jsonEncode({
      'op': 'publish',
      'topic': topic,
      'msg': msg,
    });

    _webSocket!.add(publishMsg);
  }

  /// `/drone/cmd_vel` topic'ine advertise mesajı gönderir.
  ///
  /// Rosbridge sunucusuna bu topic'e mesaj yayınlayacağımızı bildirir.
  void advertise(String topic, String type) {
    if (!isConnected || _webSocket == null) return;

    final advertiseMsg = jsonEncode({
      'op': 'advertise',
      'topic': topic,
      'type': type,
    });

    _webSocket!.add(advertiseMsg);
    _log('Advertise: $topic ($type)');
  }

  /// `/drone/cmd_vel` topic'ine Twist mesajı yayınlar.
  ///
  /// [linear]: Lineer hız vektörü {x, y, z} (m/s)
  /// [angular]: Açısal hız vektörü {x, y, z} (rad/s)
  void publishTwist({
    required Map<String, double> linear,
    required Map<String, double> angular,
  }) {
    publish('/drone/cmd_vel', 'geometry_msgs/msg/Twist', {
      'linear': {
        'x': linear['x'] ?? 0.0,
        'y': linear['y'] ?? 0.0,
        'z': linear['z'] ?? 0.0,
      },
      'angular': {
        'x': angular['x'] ?? 0.0,
        'y': angular['y'] ?? 0.0,
        'z': angular['z'] ?? 0.0,
      },
    });
  }

  /// Rosbridge publish JSON mesajını doğrudan gönderir.
  ///
  /// [json]: Tam rosbridge publish mesajı (op, topic, msg dahil)
  /// DroneCommandModel.toTwistJson() çıktısı doğrudan buraya verilebilir.
  void sendRaw(Map<String, dynamic> json) {
    if (!isConnected || _webSocket == null) {
      _log('Ham mesaj gönderilemedi: bağlantı yok');
      return;
    }

    _webSocket!.add(jsonEncode(json));
  }

  /// Bir ROS topic'ine abone olur.
  ///
  /// [topic]: Abone olunacak topic adı
  /// [type]: Mesaj tipi
  /// Döndürülen stream, bu topic'ten gelen mesajları yayınlar.
  Stream<Map<String, dynamic>> subscribe(String topic, String type) {
    // Eğer zaten abone isek mevcut stream'i döndür
    if (_topicControllers.containsKey(topic)) {
      return _topicControllers[topic]!.stream;
    }

    // Yeni stream controller oluştur
    final controller = StreamController<Map<String, dynamic>>.broadcast();
    _topicControllers[topic] = controller;

    // Rosbridge subscribe mesajı gönder
    if (isConnected && _webSocket != null) {
      final subscribeMsg = jsonEncode({
        'op': 'subscribe',
        'topic': topic,
        'type': type,
      });
      _webSocket!.add(subscribeMsg);
      _log('Abone olundu: $topic ($type)');
    }

    return controller.stream;
  }

  /// Bir topic aboneliğini iptal eder.
  void unsubscribe(String topic) {
    if (isConnected && _webSocket != null) {
      final unsubscribeMsg = jsonEncode({
        'op': 'unsubscribe',
        'topic': topic,
      });
      _webSocket!.add(unsubscribeMsg);
    }

    _topicControllers[topic]?.close();
    _topicControllers.remove(topic);
    _log('Abonelik iptal: $topic');
  }

  // ── Dahili Yöntemler ──

  /// Gelen WebSocket mesajını işler.
  void _onMessage(dynamic data) {
    try {
      final json = jsonDecode(data as String) as Map<String, dynamic>;
      final op = json['op'] as String?;

      if (op == 'publish') {
        // Topic mesajı — ilgili controller'a yönlendir
        final topic = json['topic'] as String?;
        if (topic != null && _topicControllers.containsKey(topic)) {
          _topicControllers[topic]!.add(json);
        }
      } else if (op == 'status') {
        // Rosbridge durum mesajı (hata veya onay)
        _log('Rosbridge durum: ${json['msg']}');
      }
    } catch (e) {
      _log('Mesaj ayrıştırma hatası: $e');
    }
  }

  /// WebSocket hata durumunu işler.
  void _onError(dynamic error) {
    _log('WebSocket hatası: $error');
    _updateState(RosbridgeConnectionState.error);
    _scheduleReconnect();
  }

  /// WebSocket bağlantısı kapandığında çağrılır.
  void _onDone() {
    _log('WebSocket bağlantısı kapandı');
    _heartbeatTimer?.cancel();

    if (_currentState != RosbridgeConnectionState.disconnected) {
      // Beklenmeyen kapanma — yeniden bağlan
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
    }
  }

  /// Bağlantı durumunu günceller ve stream'e yayınlar.
  void _updateState(RosbridgeConnectionState newState) {
    _currentState = newState;
    if (!_connectionStateController.isClosed) {
      _connectionStateController.add(newState);
    }
  }

  /// Yeniden bağlanma zamanlayıcısını başlatır.
  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      _log('Maksimum yeniden bağlanma denemesine ulaşıldı');
      _updateState(RosbridgeConnectionState.error);
      return;
    }

    _reconnectTimer?.cancel();
    _reconnectAttempts++;
    _updateState(RosbridgeConnectionState.reconnecting);

    _log('Yeniden bağlanma denemesi $_reconnectAttempts/$_maxReconnectAttempts '
        '(${_reconnectDelaySec}s sonra)');

    _reconnectTimer = Timer(
      Duration(seconds: _reconnectDelaySec),
      () async {
        await _establishConnection();
        // Yeniden bağlanınca mevcut abonelikleri tekrar kur
        if (isConnected) {
          _resubscribeAll();
        }
      },
    );
  }

  /// Yeniden bağlanma sonrası mevcut abonelikleri tekrar kurar.
  void _resubscribeAll() {
    // Not: Topic type bilgisi subscribe sırasında zaten gönderiliyor,
    // burada sadece rosbridge'e yeniden subscribe mesajı gönderiyoruz.
    // Type bilgisini saklamadığımız için boş string gönderiyoruz
    // (rosbridge bunu kabul eder).
    for (final topic in _topicControllers.keys) {
      if (isConnected && _webSocket != null) {
        final subscribeMsg = jsonEncode({
          'op': 'subscribe',
          'topic': topic,
        });
        _webSocket!.add(subscribeMsg);
        _log('Yeniden abone olundu: $topic');
      }
    }
  }

  /// Heartbeat (canlılık kontrolü) zamanlayıcısını başlatır.
  ///
  /// Periyodik olarak boş bir cmd_vel mesajı göndererek
  /// bağlantının canlı olduğunu doğrular.
  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(
      const Duration(seconds: _heartbeatIntervalSec),
      (_) {
        if (isConnected && _webSocket != null) {
          // Rosbridge'e basit bir "ping" benzeri kontrol
          // Boş bir service call veya status sorgusu gönderebiliriz
          try {
            _webSocket!.add(jsonEncode({
              'op': 'call_service',
              'service': '/rosapi/get_time',
              'args': {},
            }));
          } catch (e) {
            _log('Heartbeat hatası: $e');
            _onError(e);
          }
        }
      },
    );
  }

  /// Debug log mesajı yazdırır.
  void _log(String message) {
    // ignore: avoid_print
    print('[RosbridgeService] $message');
  }

  /// Servisi tamamen kapatır ve tüm kaynakları serbest bırakır.
  Future<void> dispose() async {
    await disconnect();
    await _connectionStateController.close();
  }
}
