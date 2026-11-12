# DroneVoice Mobil — Mimari

Flutter (Dart 3) ile yazılmış, paket adı `drone_voice_control`. Android paket
kimliği `com.atobasgan.telsiz`. Özellik listesi için bkz. [OZELLIKLER.md](OZELLIKLER.md).

## Genel görünüm

```
                         ┌──────────────── Telefon ────────────────┐
                         │                                         │
 Kullanıcı sesi ──▶ Sesli Uçuş Paneli (BLoC)        Telsiz modülü (ChangeNotifier)
                         │  speech_to_text (tr_TR)      │  mikrofon (record) / cihaz STT
                         │  ProcessVoiceCommand          │
                         │  SendDroneCommand (limitler)  │
                         ▼                               ▼
              rosbridge WebSocket :9090        Telsiz protokolü v1 (WebSocket)
                         │                               │
                         ▼                               ▼
         rosbridge_server / mobile_ws_bridge.py   ros2_ws/src/mobile_bridge
                         │                         (STT, command_parser,
                         ▼                          mission_executor)
          /drone/cmd_vel  ◀──  Gazebo Sim / ROS 2  ──▶  PX4
          /drone/odometry, /drone/imu ─────▶ telemetri
```

Giriş noktası [lib/main.dart](lib/main.dart):
1. `initializeDependencies()` ile get_it servislerini kurar.
2. `AyarDeposu.yukle()` ile telsiz ayarlarını okur ve `TelsizKontrolcusu` nesnesini oluşturur.
3. Kayıtlı bir adres varsa telsizi otomatik bağlar.
4. Wakelock'u açar.
5. `MultiBlocProvider` (`DroneBloc`, `VoiceBloc`, `ConnectionBloc`) ile `HomeScreen` ekranını açar.

## 1. Sesli Uçuş Paneli — Clean Architecture + BLoC

```
lib/
├── core/            sabitler (ROS topic'leri, komutlar), enum'lar, tema, hatalar, logger, izinler
├── domain/          saf Dart: varlıklar, repository arayüzleri, use case'ler
├── data/            datasource'lar, modeller, repository gerçeklemeleri
├── di/              injection_container.dart (get_it)
└── presentation/    blocs/, screens/, widgets/
```

Bağımlılık yönü `presentation → domain ← data` şeklindedir. `domain` katmanı Flutter'a ve paketlere bağımlı değildir.

### Katmanlar

| Katman | Önemli dosyalar | Görevi |
|---|---|---|
| Datasource | `speech_service.dart` | `speech_to_text` sarmalayıcısı. Sonuç ve hata stream'leri yayınlar. Her dinlemede callback'leri yeniden bağlar, çünkü `SpeechToText` telsiz modülüyle paylaşılan tekil bir nesnedir. |
| | `tts_service.dart` | `flutter_tts`, Türkçe. Cihazda Türkçe ses yoksa log'a yazar. Okumanın bitmesini beklemez. |
| | `rosbridge_service.dart` | rosbridge v2 JSON protokolü (advertise / publish / subscribe). 10 Hz yayın yapar. |
| | `local_storage_service.dart` | `shared_preferences` |
| Repository | `voice_repository_impl.dart` | Tanıma sonucunu `VoiceCommand` nesnesine çevirir (ara/final). Motor hatalarını BLoC'a iletir. |
| | `drone_repository_impl.dart` | Komut gönderir ve telemetri stream'ini sağlar. |
| | `settings_repository_impl.dart` | Güvenlik limitlerini ve tercihleri tutar. |
| Use case | `process_voice_command.dart` | Türkçe metni regex kalıplarıyla `DroneCommandType` tipine eşler. Türkçe karakterlere duyarlı kelime sınırı kullanır. |
| | `send_drone_command.dart` | Hızları `SafetyLimits` sınırlarına kırpar, sonra gönderir. |
| | `get_drone_telemetry.dart` | Telemetri stream'i |

### Ses akışı (VoiceBloc)

```
VoiceButton basılı ──▶ StartListening ──▶ VoiceListening(partialText)
     konuşma sürer ──▶ VoiceResultReceived(isFinal:false) ──▶ VoiceListening(partialText)
VoiceButton bırak  ──▶ StopListening ──▶ (final sonuç ya da son ara metin)
                   ──▶ VoiceProcessing(rawText)
                   ──▶ ProcessVoiceCommand
                   ──▶ VoiceCommandRecognized(command, rawText)  |  VoiceError(message, lastSpokenText)
```

- Her dinleme oturumunun bir kimliği (`_sessionId`) vardır. Önceki oturumdan geç gelen sonuçlar yeni oturumu bozmaz.
- `VoiceRecognitionFailed` olayı motor hatalarını `VoiceError` durumuna çevirir. Böylece ekran "dinleniyor" durumunda takılı kalmaz.

### Ekran tarafı (FlightScreen)

`VoiceCommandRecognized` durumunda ekran şunları yapar:
1. `KomutDuyurusu.komuttan(command, rawText)` ile ikon ve cümle üretir ("İleri gidiliyor"; kalkış ve iniş ayrıca ele alınır).
2. Stack üstünde `CommandPopup` gösterir (1,8 sn).
3. `TtsService.speak(cumle)` ile cümleyi sesli okur.
4. Komutu `DroneBloc` üzerinden `SendDroneCommand` ile gönderir ve geçmişe ekler.

Ekranın gövdesi tek bir `SingleChildScrollView` içindedir: telemetri, ses göstergesi, hızlı komutlar ve geçmiş. Mikrofon düğmesi altta sabittir.

### Bağımlılık enjeksiyonu
[lib/di/injection_container.dart](lib/di/injection_container.dart):
- Servisler, repository'ler ve use case'ler `registerLazySingleton` ile kaydedilir.
- BLoC'lar `registerFactory` ile kaydedilir.

## 2. Telsiz modülü

```
lib/
├── protokol/      mesajlar.dart (JSON + ikili ses çerçevesi), baglanti_adresi.dart (QR/URL çözümü)
├── baglanti/      telsiz_istemcisi.dart (WebSocket, otomatik yeniden bağlanma)
├── ses/           mikrofon.dart, cihaz_tanima.dart, halka_tampon.dart, pcm_parcalayici.dart, seviye.dart
├── durum/         telsiz_kontrolcusu.dart (uygulamanın beyni), modeller.dart, komut_aciklama.dart
├── geri_bildirim/ geri_bildirimci.dart (TTS + titreşim)
├── ayarlar/       ayarlar.dart (AyarDeposu)
├── ekranlar/      baglan_ekrani, telsiz_ekrani, ayarlar_ekrani, qr_tarayici
└── bilesenler/    ptt_dugmesi, konusma_karti, telemetri_seridi, acil_dur_dugmesi
```

`TelsizKontrolcusu` bir `ChangeNotifier` nesnesidir. Bağlantı, mikrofon, tanıma ve geri bildirim arayüz olarak verilir. Testler bu sayede sahte nesnelerle çalışır (`test/sahteler.dart`).

### Telsiz protokolü v1
Tek WebSocket bağlantısı kullanılır. Yer istasyonu tarafı `ros2_ws/src/mobile_bridge/protokol.py` dosyasındadır.
- **Metin çerçevesi:** JSON, her mesajda `tip` alanı bulunur.
  - Sunucudan gelen tipler: `hos_geldin`, `isleniyor`, `duyuldu`, `komut`, `anlasilmadi`, `geri_bildirim`, `telemetri`, `hata`.
  - Görev durumları: `yurutuyor`, `tamamlandi`, `reddedildi`.
- **İkili çerçeve:** `[uint32 konuşma id][uint32 sıra][PCM16 LE mono]`, 16 kHz.
  - Bir parça 20 ms'dir (640 bayt).

### Konuşma akışı (Yer STT modu)
```
PTT bas ──▶ ptt_basla + halka tampondaki son 300 ms ──▶ canlı 20 ms parçalar
PTT bırak ──▶ +150 ms son kayıt ──▶ ptt_bitti
        ──▶ sunucu: duyuldu → komut → yurutuyor → tamamlandi/reddedildi
        ──▶ kart güncellenir, sesli yanıt ve titreşim verilir
```
- 250 ms'den kısa basışlar yok sayılır.
- En fazla 50 kart tutulur.

## Ortak noktalar ve dikkat edilecekler
- `SpeechToText` paketi uygulama genelinde **tek örnektir**. Uçuş paneli ve telsiz aynı nesneyi kullanır. Bu yüzden `SpeechService` callback'leri her `listen` çağrısında yeniden bağlar. Yeni bir yerde tanıma kullanılacaksa bu kurala uyulmalıdır.
- İki modül iki ayrı TTS kullanır: `TtsService` ve `CihazGeriBildirimci`. Yeni sesli geri bildirimler hangi ekrana aitse o modülün servisine eklenmelidir.

## Testler
`test/` klasörü:
- Protokol, ses tamponu ve PCM parçalama
- Telsiz istemcisi ve kontrolcüsü
- Komut açıklamaları
- Komut eşleştirme (`process_voice_command_test.dart`)
- Ekran ve uyum testleri

Çalıştırmak için: `flutter test`.
