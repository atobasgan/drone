# Drone Telsizi (Flutter)

Telefonu telsiz gibi kullanarak drone'a Türkçe sesli komut verme uygulaması:
**bas, konuş, bırak**. Komut yer istasyonundaki sistemden geçer (normalize → hızlı yol / LLM →
güvenlik → PX4); telefon sonucu kart olarak gösterir ve sesli cevap verir.

Ayrıntılı açıklama: [../MOBIL_TELSIZ_ACIKLAMA.txt](../MOBIL_TELSIZ_ACIKLAMA.txt) ·
Tasarım: [../MOBIL_TELSIZ_UYGULAMASI.txt](../MOBIL_TELSIZ_UYGULAMASI.txt)

## Özellikler

- **Bas-konuş:** Dokunduğun anda dinlemeye başlar (uzun basma gecikmesi yok). 300 ms ön kayıt ve 150 ms son kayıt olduğu için ilk ve son hece kesilmez. 250 ms'den kısa basışlar yok sayılır.
- **İki tanıma modu:**
  - **Yer STT:** Ham ses 20 ms'lik parçalar halinde yer istasyonuna akar ve orada faster-whisper ile yazıya çevrilir.
  - **Telefon STT:** Telefonun kendi Türkçe tanıyıcısı çalışır, yer istasyonuna sadece metin gider.
  - **Otomatik:** Yer istasyonunda STT varsa onu, yoksa telefonu kullanır.
- **ACİL DUR:** Her ekranda görünür, tek dokunuşla çalışır. LLM ve STT'ye uğramaz. İzleyiciler de basabilir.
- **Konuşma kartları:** Her konuşma için duyulan metin, normalize hali, **LLM'in ya da hızlı yolun ürettiği JSON**, komutun kaynağı (HIZLI YOL / LLM / ACİL), uçtan uca gecikme ve yürütme durumu (yürütüyor / tamam / reddedildi + sebep) görünür.
- **Telemetri şeridi:** İrtifa, hız, yön, batarya, PX4 modu, arm ve havada/yerde bilgisi.
- **Türkçe sesli yanıt ve titreşim:** "20 metre yükseliyorum", "Reddedildi…", "Anlamadım".
- **Komut girişleri:** Hızlı tuşlar (kalk, in, eve dön…) ve klavyeyle komut. Bunlar da metin olarak gider ve güvenlik katmanından geçer.
- **Bağlantı:** QR kodla tek adımda bağlanma, token ile kimlik doğrulama, tek operatör + izleyiciler, otomatik yeniden bağlanma ve ping göstergesi.
- **Ekran:** Kullanım sırasında ekran kararmaz. Koyu ve yüksek kontrastlı tema.

## Çalıştırma

```bash
# 1) Yer istasyonu — ROS'suz deneme (gerçek parser + güvenlik, sanal drone):
./scripts/telsiz_deneme.sh                         # + --llm http://127.0.0.1:8080, --stt faster_whisper
#    ya da tam sistem:
ros2 launch drone_bringup telsiz.launch.py

# 2) Telefon (aynı Wi-Fi):
cd mobil && flutter pub get && flutter run
#    Uygulamada "QR kodu okut" -> terminaldeki QR kodu.
```

## Klasörler

```
lib/
  protokol/    mesajlar.dart (JSON + ikili ses çerçevesi), baglanti_adresi.dart (QR/adres çözümü)
  ses/         mikrofon.dart (record, 16 kHz PCM), cihaz_tanima.dart (speech_to_text),
               halka_tampon.dart (ön kayıt), pcm_parcalayici.dart (20 ms), seviye.dart
  baglanti/    telsiz_istemcisi.dart (WebSocket, ping, yeniden bağlanma)
  durum/       telsiz_kontrolcusu.dart (uygulamanın beyni), modeller.dart, komut_aciklama.dart
  geri_bildirim/ geri_bildirimci.dart (Türkçe TTS + titreşim)
  ayarlar/     ayarlar.dart (shared_preferences)
  ekranlar/    baglan, telsiz (ana), ayarlar, qr_tarayici
  bilesenler/  ptt_dugmesi, acil_dur_dugmesi, konusma_karti, telemetri_seridi
test/          saf mantık, kontrolcü (sahtelerle), WebSocket istemcisi (gerçek sunucu),
               ekran testi, uyum_test.dart (gerçek Python köprüsüyle)
```

## Testler

```bash
flutter analyze && flutter test            # 29 test
../scripts/telsiz_uyum_testi.sh            # Dart istemcisi <-> Python köprüsü (gerçek)
```
