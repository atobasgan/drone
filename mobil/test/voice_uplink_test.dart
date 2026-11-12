import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:drone_voice_control/core/constants/ros_constants.dart';
import 'package:drone_voice_control/core/utils/connection_log.dart';
import 'package:drone_voice_control/data/datasources/rosbridge_service.dart';
import 'package:drone_voice_control/data/datasources/voice_recorder.dart';
import 'package:drone_voice_control/data/models/audio_clip_message.dart';
import 'package:drone_voice_control/data/models/backend_feedback_model.dart';
import 'package:drone_voice_control/data/models/voice_text_message.dart';
import 'package:drone_voice_control/data/repositories/voice_uplink_repository_impl.dart';
import 'package:drone_voice_control/domain/entities/audio_clip.dart';
import 'package:drone_voice_control/domain/entities/backend_feedback.dart';
import 'package:drone_voice_control/domain/repositories/voice_uplink_repository.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_event.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_state.dart';
import 'package:drone_voice_control/ses/mikrofon.dart';
import 'package:flutter_test/flutter_test.dart';

/// WebSocket açmadan rosbridge çağrılarını kaydeden sahte servis.
class _SahteRosbridge implements RosbridgeService {
  final _durum = StreamController<RosbridgeConnectionState>.broadcast(sync: true);
  final konular = <String, StreamController<Map<String, dynamic>>>{};
  final advertised = <(String, String)>[];
  final published = <(String, Map<String, dynamic>)>[];
  bool bagli = false;

  @override
  final ConnectionLog log = ConnectionLog();

  void baglan() {
    bagli = true;
    _durum.add(RosbridgeConnectionState.connected);
  }

  @override
  bool get isConnected => bagli;

  @override
  Stream<RosbridgeConnectionState> get connectionStateStream => _durum.stream;

  @override
  void advertise(String topic, String type) => advertised.add((topic, type));

  @override
  void publish(String topic, String type, Map<String, dynamic> msg) =>
      published.add((topic, msg));

  @override
  Stream<Map<String, dynamic>> subscribe(String topic, String type) => konular
      .putIfAbsent(topic, () => StreamController.broadcast(sync: true))
      .stream;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// Mikrofon yerine: açılınca verilen PCM parçalarını gönderir.
class _SahteMikrofon implements SesKaynagi {
  _SahteMikrofon(this.parcalar, {this.izin = true});

  final List<Uint8List> parcalar;
  final bool izin;
  @override
  bool acik = false;

  @override
  Future<bool> izinIste() async => izin;

  @override
  Future<void> ac(void Function(Uint8List veri) veri, {bool gurultuBastirma = false}) async {
    acik = true;
    for (final p in parcalar) {
      veri(p);
    }
  }

  @override
  Future<void> kapat() async => acik = false;
}

class _SahteUplink implements VoiceUplinkRepository {
  final sesler = <AudioClip>[];
  final metinler = <String>[];
  bool bagli = true;

  @override
  bool sendAudioClip(AudioClip clip) {
    if (!bagli) return false;
    sesler.add(clip);
    return true;
  }

  @override
  bool sendRawText(String text) {
    if (!bagli) return false;
    metinler.add(text);
    return true;
  }

  @override
  Stream<String> get transcriptStream => const Stream.empty();

  @override
  Stream<BackendFeedback> get feedbackStream => const Stream.empty();
}

/// [ms] süreli sessiz PCM16 (16 kHz mono)
Uint8List _pcm(int ms) => Uint8List(16000 * 2 * ms ~/ 1000);

VoiceRecorder _kayitci(List<Uint8List> parcalar, {bool izin = true}) => VoiceRecorder(
      source: _SahteMikrofon(parcalar, izin: izin),
      tail: Duration.zero,
    );

Future<List<VoiceState>> _calistir(VoiceBloc bloc, List<VoiceEvent> olaylar) async {
  final durumlar = <VoiceState>[];
  final sub = bloc.stream.listen(durumlar.add);
  for (final o in olaylar) {
    bloc.add(o);
  }
  await Future<void>.delayed(const Duration(milliseconds: 20));
  await sub.cancel();
  await bloc.close();
  return durumlar;
}

void main() {
  group('AudioClipMessage', () {
    test('geçerli WAV başlığı üretir', () {
      final pcm = Uint8List.fromList([1, 0, 2, 0, 3, 0, 4, 0]);
      final wav = AudioClipMessage.fromClip(AudioClip(pcm: pcm, sampleRate: 16000)).wav;
      final h = ByteData.sublistView(wav);

      expect(ascii.decode(wav.sublist(0, 4)), 'RIFF');
      expect(h.getUint32(4, Endian.little), 36 + pcm.length);
      expect(ascii.decode(wav.sublist(8, 16)), 'WAVEfmt ');
      expect(h.getUint16(20, Endian.little), 1, reason: 'PCM');
      expect(h.getUint16(22, Endian.little), 1, reason: 'mono');
      expect(h.getUint32(24, Endian.little), 16000);
      expect(h.getUint32(28, Endian.little), 32000, reason: 'bayt/sn');
      expect(h.getUint16(34, Endian.little), 16, reason: 'bit');
      expect(ascii.decode(wav.sublist(36, 40)), 'data');
      expect(h.getUint32(40, Endian.little), pcm.length);
      expect(wav.sublist(44), pcm);
    });

    test('rosbridge msg: UInt8MultiArray, data base64 WAV', () {
      final mesaj = AudioClipMessage.fromClip(AudioClip(pcm: _pcm(100), sampleRate: 16000));
      final ros = mesaj.toRosMsg();
      expect(base64Decode(ros['data'] as String), mesaj.wav);
      expect(ros['layout'], {'dim': [], 'data_offset': 0});
    });
  });

  group('VoiceRecorder', () {
    test('parçaları birleştirir, süre hesaplanır', () async {
      final r = _kayitci([_pcm(200), _pcm(300)]);
      expect(await r.start(), isTrue);
      final clip = await r.stop();
      expect(clip.durationMs, 500);
      expect(clip.sampleRate, 16000);
      expect(r.isRecording, isFalse);
    });

    test('azami süreyi aşan ses atılır', () async {
      final r = VoiceRecorder(
        source: _SahteMikrofon([_pcm(800), _pcm(800)]),
        maxDuration: const Duration(seconds: 1),
        tail: Duration.zero,
      );
      await r.start();
      expect((await r.stop()).durationMs, lessThanOrEqualTo(1000));
    });

    test('izin yoksa başlamaz', () async {
      expect(await _kayitci([], izin: false).start(), isFalse);
    });
  });

  group('VoiceUplinkRepositoryImpl', () {
    test('bağlanınca konular advertise edilir; ses /voice/audio, metin /voice/text', () {
      final ros = _SahteRosbridge();
      final repo = VoiceUplinkRepositoryImpl(rosbridgeService: ros);
      final clip = AudioClip(pcm: _pcm(500), sampleRate: 16000);

      expect(repo.sendAudioClip(clip), isFalse, reason: 'bağlantı yokken gönderilmez');
      ros.baglan();
      expect(ros.advertised, [
        (RosConstants.voiceAudioTopic, RosConstants.audioMsgType),
        (RosConstants.voiceTextTopic, RosConstants.stringMsgType),
      ]);

      expect(repo.sendAudioClip(clip), isTrue);
      expect(ros.published.last.$1, '/voice/audio');
      final wav = base64Decode(ros.published.last.$2['data'] as String);
      expect(ascii.decode(wav.sublist(0, 4)), 'RIFF');
      expect(wav.length, 44 + clip.pcm.length);

      const ham = 'Önce 20 metre YÜKSEL, sonra kuzeye 50 metre git.';
      expect(repo.sendRawText(ham), isTrue);
      expect(ros.published.last.$1, '/voice/text');
      expect(ros.published.last.$2, {'data': ham});
      expect(repo.sendAudioClip(AudioClip(pcm: Uint8List(0), sampleRate: 16000)), isFalse);
    });

    test('/voice/text ve /drone/feedback akışlara düşer', () async {
      final ros = _SahteRosbridge()..bagli = true;
      final repo = VoiceUplinkRepositoryImpl(rosbridgeService: ros);
      final metinler = <String>[];
      final geri = <BackendFeedback>[];
      repo.transcriptStream.listen(metinler.add);
      repo.feedbackStream.listen(geri.add);

      ros.konular['/voice/text']!.add({'op': 'publish', 'msg': {'data': 'kalk'}});
      ros.konular['/drone/feedback']!.add({
        'op': 'publish',
        'msg': {'durum': 'reddedildi', 'mesaj': 'anlamadım'},
      });
      ros.konular['/drone/feedback']!.add({'op': 'publish', 'msg': 'bozuk'});
      await Future<void>.delayed(Duration.zero);

      expect(metinler, ['kalk']);
      expect(geri, [const BackendFeedback(durum: 'reddedildi', mesaj: 'anlamadım')]);
      expect(ros.log.entries.map((e) => e.level),
          containsAll([LogLevel.error, LogLevel.warning]));
    });
  });

  group('VoiceBloc', () {
    test('bas-konuş: kayıt WAV olarak gönderilir, metin üretilmez', () async {
      final uplink = _SahteUplink();
      final durumlar = await _calistir(
        VoiceBloc(voiceRecorder: _kayitci([_pcm(600)]), voiceUplinkRepository: uplink),
        const [StartListening(), StopListening()],
      );
      expect(durumlar.first, isA<VoiceListening>());
      expect(durumlar.last, const VoiceAudioSent(durationMs: 600, sequence: 1));
      expect(uplink.sesler.single.durationMs, 600);
      expect(uplink.metinler, isEmpty);
    });

    test('çok kısa kayıt gönderilmez', () async {
      final uplink = _SahteUplink();
      final durumlar = await _calistir(
        VoiceBloc(voiceRecorder: _kayitci([_pcm(100)]), voiceUplinkRepository: uplink),
        const [StartListening(), StopListening()],
      );
      expect(durumlar.last, isA<VoiceError>());
      expect(uplink.sesler, isEmpty);
    });

    test('bağlantı yoksa VoiceError', () async {
      final uplink = _SahteUplink()..bagli = false;
      final durumlar = await _calistir(
        VoiceBloc(voiceRecorder: _kayitci([_pcm(600)]), voiceUplinkRepository: uplink),
        const [StartListening(), StopListening()],
      );
      expect(durumlar.last, isA<VoiceError>());
    });

    test('hızlı komut metni yorumlanmadan /voice/text\'e gider', () async {
      final uplink = _SahteUplink();
      final durumlar = await _calistir(
        VoiceBloc(voiceRecorder: _kayitci([]), voiceUplinkRepository: uplink),
        const [VoiceResultReceived(text: 'kalk ve otuz metre ileri git')],
      );
      expect(uplink.metinler, ['kalk ve otuz metre ileri git']);
      expect(durumlar.last, isA<VoiceTextSent>());
    });
  });

  group('veri modelleri', () {
    test('eşitlik, hashCode ve toString', () {
      expect(const VoiceTextMessage('dur'), const VoiceTextMessage('dur'));
      expect(const VoiceTextMessage('dur').hashCode, const VoiceTextMessage('dur').hashCode);

      const a = BackendFeedback(durum: 'kabul', mesaj: '2 adım');
      expect(a, const BackendFeedback(durum: 'kabul', mesaj: '2 adım'));
      expect(a == const BackendFeedback(durum: 'hata', mesaj: '2 adım'), isFalse);

      final c1 = AudioClip(pcm: Uint8List.fromList([1, 2]), sampleRate: 16000);
      final c2 = AudioClip(pcm: Uint8List.fromList([1, 2]), sampleRate: 16000);
      final c3 = AudioClip(pcm: Uint8List.fromList([1, 3]), sampleRate: 16000);
      expect(c1, c2);
      expect(c1.hashCode, c2.hashCode);
      expect(c1 == c3, isFalse);
      expect(c1.toString(), contains('16000 Hz'));

      expect(AudioClipMessage.fromClip(c1), AudioClipMessage.fromClip(c2));
    });

    test('BackendFeedbackModel eksik alanda null döner', () {
      expect(BackendFeedbackModel.fromRosbridgeJson({'msg': {'durum': 'kabul'}}), isNull);
    });
  });

  test('ConnectionLog kapasiteyi aşınca en eskiyi atar', () {
    final log = ConnectionLog(capacity: 2)
      ..info('a', '1')
      ..info('a', '2')
      ..error('a', '3');
    expect(log.entries.map((e) => e.message), ['2', '3']);
  });
}
