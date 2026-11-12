import 'dart:async';
import 'package:drone_voice_control/core/constants/ros_constants.dart';
import 'package:drone_voice_control/data/datasources/rosbridge_service.dart';
import 'package:drone_voice_control/data/models/drone_telemetry_model.dart';
import 'package:drone_voice_control/domain/entities/drone_telemetry.dart';
import 'package:drone_voice_control/domain/repositories/drone_repository.dart';

class DroneRepositoryImpl implements DroneRepository {
  final RosbridgeService rosbridgeService;
  final _telemetryController = StreamController<DroneTelemetry>.broadcast();
  final _statusController = StreamController<DroneConnectionStatus>.broadcast();

  StreamSubscription? _rosStateSub;
  StreamSubscription? _odomSub;
  StreamSubscription? _imuSub;

  double _currentRoll = 0.0;
  double _currentPitch = 0.0;
  double _currentYaw = 0.0;

  DroneConnectionStatus _currentStatus = DroneConnectionStatus.disconnected;

  DroneRepositoryImpl({required this.rosbridgeService}) {
    _rosStateSub = rosbridgeService.connectionStateStream.listen(_handleConnectionState);
  }

  void _handleConnectionState(RosbridgeConnectionState state) {
    switch (state) {
      case RosbridgeConnectionState.connected:
        _currentStatus = DroneConnectionStatus.connected;
        _setupSubscriptions();
        break;
      case RosbridgeConnectionState.connecting:
        _currentStatus = DroneConnectionStatus.connecting;
        break;
      case RosbridgeConnectionState.reconnecting:
        _currentStatus = DroneConnectionStatus.reconnecting;
        break;
      case RosbridgeConnectionState.error:
        _currentStatus = DroneConnectionStatus.error;
        break;
      case RosbridgeConnectionState.disconnected:
        _currentStatus = DroneConnectionStatus.disconnected;
        break;
    }
    _statusController.add(_currentStatus);
  }

  void _setupSubscriptions() {
    // Odometri aboneliği
    _odomSub?.cancel();
    _odomSub = rosbridgeService
        .subscribe(RosConstants.odometryTopic, RosConstants.odometryType)
        .listen((msg) {
      try {
        final telemetry = DroneTelemetryModel.fromRosbridgeJson(
          msg,
          roll: _currentRoll,
          pitch: _currentPitch,
          yaw: _currentYaw,
        );
        _telemetryController.add(telemetry);
      } catch (e) {
        // Ayrıştırma hatası yoksayılabilir
      }
    });

    // IMU aboneliği
    _imuSub?.cancel();
    _imuSub = rosbridgeService
        .subscribe(RosConstants.imuTopic, RosConstants.imuType)
        .listen((msg) {
      try {
        final innerMsg = msg['msg'] as Map<String, dynamic>?;
        if (innerMsg != null && innerMsg.containsKey('orientation')) {
          final orient = innerMsg['orientation'] as Map<String, dynamic>;
          final x = (orient['x'] as num?)?.toDouble() ?? 0.0;
          final y = (orient['y'] as num?)?.toDouble() ?? 0.0;
          final z = (orient['z'] as num?)?.toDouble() ?? 0.0;
          final w = (orient['w'] as num?)?.toDouble() ?? 1.0;

          // Basit Quaternion -> Euler dönüşümü
          _currentYaw = 2.0 * (w * z + x * y);
          _currentRoll = 2.0 * (w * x + y * z);
          _currentPitch = 2.0 * (w * y - z * x);
        }
      } catch (e) {
        // IMU ayrıştırma hatası yoksayılabilir
      }
    });
  }

  @override
  Future<bool> connect({required String host, required int port}) async {
    return await rosbridgeService.connect(host, port);
  }

  @override
  Future<void> disconnect() async {
    await _odomSub?.cancel();
    await _imuSub?.cancel();
    await rosbridgeService.disconnect();
  }

  @override
  Stream<DroneTelemetry> get telemetryStream => _telemetryController.stream;

  @override
  Stream<DroneConnectionStatus> get connectionStatus => _statusController.stream;

  @override
  DroneConnectionStatus get currentConnectionStatus => _currentStatus;

  @override
  Stream<bool> get connectionStream => rosbridgeService.connectionStateStream
      .map((state) => state == RosbridgeConnectionState.connected);

  @override
  bool get isConnected => rosbridgeService.isConnected;

  @override
  String? get currentHost => rosbridgeService.host;

  @override
  int? get currentPort => rosbridgeService.port;

  void dispose() {
    _rosStateSub?.cancel();
    _odomSub?.cancel();
    _imuSub?.cancel();
    _telemetryController.close();
    _statusController.close();
  }
}

