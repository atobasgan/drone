/// RosbridgeService - Rosbridge WebSocket üzerinden ROS 2 iletişim servisi.
///
/// ROS 2 tarafıyla rosbridge_websocket aracılığıyla iletişim kurar.
/// Rosbridge v2.0 protokolü JSON mesajları kullanılır.
///
/// Kullanılan topic'ler:
/// - `/voice/text` (std_msgs/String) → ham sesli komut metni yayınlama
/// - `/drone/feedback` (drone_interfaces/Feedback) → backend geri bildirimi
/// - `/drone/odometry` (nav_msgs/Odometry) → konum ve hız aboneliği
/// - `/drone/imu` (sensor_msgs/Imu) → ivmeölçer ve jiroskop aboneliği
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:drone_voice_control/core/utils/connection_log.dart';

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
  RosbridgeService({ConnectionLog? log}) : log = log ?? ConnectionLog();

  /// Bağlantı, gönderim ve rosbridge yanıtlarının günlüğü (Log ekranı)
  final ConnectionLog log;

  /// Heartbeat çağrılarının kimlik → gönderim zamanı eşlemesi (RTT ölçümü)
  final Map<String, DateTime> _pendingPings = {};
  int _pingCounter = 0;

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
      log.success('bağlantı', 'WebSocket açıldı: $uri');

      // Gelen mesajları dinle
      _webSocket!.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
        cancelOnError: false,
      );

      // Heartbeat başlat; ilk gidiş-dönüş kontrolü hemen yapılır
      _startHeartbeat();
      _sendPing();

      return true;
    } on SocketException catch (e) {
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
      // SocketException: Bağlantı hatası
      log.error('bağlantı', 'Bağlantı hatası: $e');
      return false;
    } on TimeoutException {
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
      log.error('bağlantı', 'Bağlantı zaman aşımı (10 s): ws://$_host:$_port');
      return false;
    } catch (e) {
      _updateState(RosbridgeConnectionState.error);
      _scheduleReconnect();
      log.error('bağlantı', 'Beklenmeyen bağlantı hatası: $e');
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
  /// [topic]: Hedef topic adı (ör. "/voice/text")
  /// [type]: Mesaj tipi (ör. "std_msgs/msg/String")
  /// [msg]: Yayınlanacak mesaj içeriği
  void publish(String topic, String type, Map<String, dynamic> msg) {
    if (!isConnected || _webSocket == null) {
      log.error('gönderim', '$topic yayınlanamadı: bağlantı yok');
      return;
    }

    final publishMsg = jsonEncode({
      'op': 'publish',
      'topic': topic,
      'msg': msg,
    });

    try {
      _webSocket!.add(publishMsg);
      log.success('gönderim',
          'publish $topic ${_summary(msg)} (${publishMsg.length} bayt)');
    } catch (e) {
      log.error('gönderim', '$topic yazılamadı: $e');
    }
  }

  /// Bir topic'e advertise mesajı gönderir.
  ///
  /// Rosbridge sunucusuna bu topic'e hangi tipte mesaj yayınlayacağımızı bildirir.
  void advertise(String topic, String type) {
    if (!isConnected || _webSocket == null) return;

    final advertiseMsg = jsonEncode({
      'op': 'advertise',
      'topic': topic,
      'type': type,
    });

    _webSocket!.add(advertiseMsg);
    log.info('gönderim', 'advertise $topic ($type)');
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
      log.info('abonelik', 'subscribe $topic ($type)');
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
      } else if (op == 'service_response') {
        _onServiceResponse(json);
      } else if (op == 'status') {
        // Rosbridge durum mesajı: reddedilen publish/advertise burada bildirilir
        final level = json['level'] as String? ?? '';
        final text = 'rosbridge $level: ${json['msg']}';
        if (level == 'error') {
          log.error('rosbridge', text);
        } else if (level == 'warning') {
          log.warning('rosbridge', text);
        } else {
          log.info('rosbridge', text);
        }
      }
    } catch (e) {
      log.warning('rosbridge', 'Mesaj ayrıştırma hatası: $e');
    }
  }

  /// WebSocket hata durumunu işler.
  void _onError(dynamic error) {
    log.error('bağlantı', 'WebSocket hatası: $error');
    _updateState(RosbridgeConnectionState.error);
    _scheduleReconnect();
  }

  /// WebSocket bağlantısı kapandığında çağrılır.
  void _onDone() {
    log.warning('bağlantı', 'WebSocket kapandı (kod: ${_webSocket?.closeCode})');
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
      log.error('bağlantı', 'Maksimum yeniden bağlanma denemesine ulaşıldı');
      _updateState(RosbridgeConnectionState.error);
      return;
    }

    _reconnectTimer?.cancel();
    _reconnectAttempts++;
    _updateState(RosbridgeConnectionState.reconnecting);

    log.warning('bağlantı',
        'Yeniden bağlanma denemesi $_reconnectAttempts/$_maxReconnectAttempts '
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
  /// Periyodik olarak `/rosapi/get_time` servis çağrısı göndererek
  /// bağlantının canlı olduğunu doğrular.
  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(
      const Duration(seconds: _heartbeatIntervalSec),
      (_) {
        if (isConnected && _webSocket != null) _sendPing();
      },
    );
  }

  /// `/rosapi/get_time` çağrısı gönderir; yanıt [_onServiceResponse]'ta ölçülür.
  void _sendPing() {
    final id = 'ping_${++_pingCounter}';
    // Yanıtı gelmeyen eski çağrılar birikmesin
    if (_pendingPings.length > 10) {
      log.warning('heartbeat', '${_pendingPings.length} heartbeat yanıtsız kaldı');
      _pendingPings.clear();
    }
    _pendingPings[id] = DateTime.now();
    try {
      _webSocket!.add(jsonEncode({
        'op': 'call_service',
        'id': id,
        'service': '/rosapi/get_time',
        'args': {},
      }));
    } catch (e) {
      log.error('heartbeat', 'Heartbeat gönderilemedi: $e');
      _onError(e);
    }
  }

  /// Heartbeat yanıtı: rosbridge'in iletişim onayı ve gidiş-dönüş süresi.
  void _onServiceResponse(Map<String, dynamic> json) {
    final id = json['id'] as String?;
    final sentAt = id == null ? null : _pendingPings.remove(id);
    if (sentAt == null) return;
    final rtt = DateTime.now().difference(sentAt).inMilliseconds;
    if (json['result'] == true) {
      log.success('heartbeat', '/rosapi/get_time yanıtı: OK ($rtt ms)');
    } else {
      log.warning('heartbeat',
          '/rosapi/get_time başarısız ($rtt ms): ${json['values']} — rosapi düğümü çalışıyor mu?');
    }
  }

  /// Günlük için mesaj özeti: uzun metin alanları (base64 ses) kısaltılır.
  static String _summary(Map<String, dynamic> msg) => jsonEncode(msg.map(
        (k, v) => MapEntry(
            k, v is String && v.length > 120 ? '<${v.length} karakter>' : v),
      ));

  /// Genel bilgi kaydı.
  void _log(String message) => log.info('rosbridge', message);

  /// Servisi tamamen kapatır ve tüm kaynakları serbest bırakır.
  Future<void> dispose() async {
    await disconnect();
    await _connectionStateController.close();
  }
}
