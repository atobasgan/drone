import 'dart:async';

import 'package:drone_voice_control/core/constants/ros_constants.dart';
import 'package:drone_voice_control/data/datasources/rosbridge_service.dart';
import 'package:drone_voice_control/data/models/audio_clip_message.dart';
import 'package:drone_voice_control/data/models/backend_feedback_model.dart';
import 'package:drone_voice_control/data/models/voice_text_message.dart';
import 'package:drone_voice_control/domain/entities/audio_clip.dart';
import 'package:drone_voice_control/domain/entities/backend_feedback.dart';
import 'package:drone_voice_control/domain/repositories/voice_uplink_repository.dart';

/// Rosbridge üzerinden `/voice/audio` ve `/voice/text` yayıncısı,
/// `/voice/text` ve `/drone/feedback` abonesi.
///
/// Her bağlantı kurulduğunda (ilk bağlantı ve yeniden bağlanma) konular
/// `advertise` edilir ve abonelikler yenilenir; rosbridge, tipi bildirilmemiş
/// bir konuya gelen `publish` isteğini reddeder.
class VoiceUplinkRepositoryImpl implements VoiceUplinkRepository {
  final RosbridgeService _ros;
  final _feedbackController = StreamController<BackendFeedback>.broadcast();
  final _transcriptController = StreamController<String>.broadcast();
  StreamSubscription<RosbridgeConnectionState>? _stateSub;
  StreamSubscription<Map<String, dynamic>>? _feedbackSub;
  StreamSubscription<Map<String, dynamic>>? _transcriptSub;

  VoiceUplinkRepositoryImpl({required RosbridgeService rosbridgeService})
      : _ros = rosbridgeService {
    _stateSub = _ros.connectionStateStream.listen((state) {
      if (state == RosbridgeConnectionState.connected) _onConnected();
    });
    if (_ros.isConnected) _onConnected();
  }

  void _onConnected() {
    _ros.advertise(RosConstants.voiceAudioTopic, RosConstants.audioMsgType);
    _ros.advertise(RosConstants.voiceTextTopic, RosConstants.stringMsgType);

    _feedbackSub?.cancel();
    _feedbackSub = _ros
        .subscribe(RosConstants.feedbackTopic, RosConstants.feedbackMsgType)
        .listen(_onFeedback);

    _transcriptSub?.cancel();
    _transcriptSub = _ros
        .subscribe(RosConstants.voiceTextTopic, RosConstants.stringMsgType)
        .listen((json) {
      final msg = json['msg'];
      final data = msg is Map ? msg['data'] : null;
      if (data is! String || _transcriptController.isClosed) return;
      _ros.log.info('backend', '${RosConstants.voiceTextTopic} "$data"');
      _transcriptController.add(data);
    });
  }

  void _onFeedback(Map<String, dynamic> json) {
    final feedback = BackendFeedbackModel.fromRosbridgeJson(json);
    if (feedback == null) {
      _ros.log.warning('backend', 'Tanınmayan /drone/feedback çerçevesi: $json');
      return;
    }
    final text = '${RosConstants.feedbackTopic} [${feedback.durum}] ${feedback.mesaj}';
    if (feedback.isNegative) {
      _ros.log.error('backend', text);
    } else {
      _ros.log.success('backend', text);
    }
    if (!_feedbackController.isClosed) _feedbackController.add(feedback);
  }

  @override
  bool sendAudioClip(AudioClip clip) {
    if (clip.pcm.isEmpty) return false;
    if (!_ros.isConnected) {
      _ros.log.error('gönderim', 'Ses kaydı gönderilemedi: rosbridge bağlantısı yok ($clip)');
      return false;
    }
    final message = AudioClipMessage.fromClip(clip);
    _ros.log.info('gönderim',
        'Ses kaydı: ${clip.durationMs} ms, ${clip.sampleRate} Hz → ${message.wav.length} bayt WAV');
    _ros.publish(
      RosConstants.voiceAudioTopic,
      RosConstants.audioMsgType,
      message.toRosMsg(),
    );
    return true;
  }

  @override
  bool sendRawText(String text) {
    if (text.trim().isEmpty) return false;
    if (!_ros.isConnected) {
      _ros.log.error('gönderim', '"$text" gönderilemedi: rosbridge bağlantısı yok');
      return false;
    }
    _ros.publish(
      RosConstants.voiceTextTopic,
      RosConstants.stringMsgType,
      VoiceTextMessage(text).toRosMsg(),
    );
    return true;
  }

  @override
  Stream<String> get transcriptStream => _transcriptController.stream;

  @override
  Stream<BackendFeedback> get feedbackStream => _feedbackController.stream;

  Future<void> dispose() async {
    await _stateSub?.cancel();
    await _feedbackSub?.cancel();
    await _transcriptSub?.cancel();
    await _feedbackController.close();
    await _transcriptController.close();
  }
}
