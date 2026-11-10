import 'package:drone_voice_control/domain/entities/drone_command.dart';
import 'package:drone_voice_control/domain/repositories/settings_repository.dart';
import 'package:drone_voice_control/domain/usecases/process_voice_command.dart';
import 'package:flutter_test/flutter_test.dart';

class _SahteAyarlar implements SettingsRepository {
  @override
  Future<SafetyLimits> getSafetyLimits() async => SafetyLimits.defaults;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  Future<DroneCommandType?> tur(String metin) async {
    final sonuc = await ProcessVoiceCommand(_SahteAyarlar())(rawText: metin);
    return sonuc.parsedCommand?.commandType;
  }

  test('ı/ş/ğ ile biten Türkçe kelimeler eşleşir', () async {
    expect(await tur('kalkış'), DroneCommandType.moveUp);
    expect(await tur('kalkış yap'), DroneCommandType.moveUp);
    expect(await tur('yukarı'), DroneCommandType.moveUp);
    expect(await tur('aşağı'), DroneCommandType.moveDown);
    expect(await tur('iniş'), DroneCommandType.moveDown);
  });

  test('tanıyıcının büyük harfle başlattığı metin eşleşir', () async {
    expect(await tur('İleri git'), DroneCommandType.moveForward);
    expect(await tur('Yüksel'), DroneCommandType.moveUp);
    expect(await tur('Sağa dön'), DroneCommandType.rotateRight);
    expect(await tur('Sola git'), DroneCommandType.moveLeft);
  });

  test('kelime içinde geçen parçalar yanlış eşleşmez', () async {
    // "kal" (dur) kalıbı "kalkış" içinde eşleşmemeli
    expect(await tur('kalkış'), isNot(DroneCommandType.hover));
    expect(await tur('dur'), DroneCommandType.hover);
    expect(await tur('merhaba'), isNull);
  });
}
