# DroneVoice Mobil — Özellikler

Sesli komutla drone kontrol eden Flutter uygulaması. Gazebo Sim + ROS 2 (Jazzy)
simülasyonundaki drone'a ve yer istasyonundaki telsiz köprüsüne bağlanır.
Arayüz ve sesli yanıtlar Türkçedir.

Uygulamada iki ses hattı vardır:

| | Sesli Uçuş Paneli | Telsiz |
|---|---|---|
| Ekran | Ana ekran → "SESLİ UÇUŞ KONTROL PANELİ" | Ana ekran → Telsiz |
| Konuşmayı anlama | Telefonda (`ProcessVoiceCommand`, kural tabanlı) | Yer istasyonunda (normalize, hızlı yol, LLM, güvenlik) |
| Drone'a ulaşma | rosbridge WebSocket → `/drone/cmd_vel` | Telsiz protokolü (JSON + ikili ses) |

## Sesli Uçuş Paneli

### Konuşma ve tanıma
- **Bas-konuş mikrofon düğmesi:** Düğme basılı tutulduğu sürece dinler, bırakılınca komut işlenir.
- **Türkçe konuşma tanıma:** `speech_to_text` ile `tr_TR`. Kısa duraksamalarda kesilmemesi için duraklama süresi 10 sn.
- **Canlı metin:** Konuşurken söylenen metin ekrandaki ses göstergesinde anlık görünür (ara sonuçlar).
- **Hata bildirimi:** "Anlaşılamadı", "internet yok", "Türkçe dil paketi yok" gibi motor hataları ekranda gösterilir.

### Komut eşleştirme
Söylenen metin aşağıdaki komutlara çevrilir (büyük/küçük harf ve Türkçe karakter farkları tolere edilir):

| Söylenen | Komut | Sesli / pop-up yanıt |
|---|---|---|
| ileri, ileri git | İleri | "İleri gidiliyor" |
| geri, geri gel | Geri | "Geri gidiliyor" |
| sol, sola git | Sola git | "Sola gidiliyor" |
| sağ, sağa git | Sağa git | "Sağa gidiliyor" |
| yukarı, yüksel | Yüksel | "Yükseliniyor" |
| kalkış | Kalkış | "Kalkış yapılıyor" |
| aşağı, alçal | Alçal | "Alçalınıyor" |
| iniş | İniş | "İniş yapılıyor" |
| sola dön / sağa dön | Dönüş | "Sola/Sağa dönülüyor" |
| dur, bekle, stop | Dur | "Durduruluyor, havada bekleniyor" |

### Geri bildirim
- **Komut pop-up'ı:** Eşleşen komut ekranın ortasında ikon, "X KOMUTU ALINDI" başlığı, yapılan iş ve söylenen metinle gösterilir. 1,8 sn sonra ya da dokununca kapanır.
- **Sesli onay (TTS):** Aynı cümle Türkçe sesle okunur (ör. "İleri gidiliyor"). Mikrofona basınca konuşma susar.
- **Komut geçmişi:** Her komut "söylenen → yapılan" biçiminde listelenir, en yenisi üstte.

### Uçuş ve güvenlik
- **Hızlı komut düğmeleri:** Kalkış, İleri, Geri vb. konuşmadan da gönderilebilir.
- **DURDUR düğmesi:** Üst çubukta, drone'u anında durdurur.
- **Güvenlik limitleri:** Doğrusal ve açısal hızlar ayarlardaki sınırlara kırpılır (`SendDroneCommand`).
- **Telemetri:** Yükseklik, hız, yön (pusula) ve batarya `/drone/odometry` ile `/drone/imu` üzerinden canlı gösterilir.
- **Uçuş geçmişi ve loglar:** Ayrı ekranda.

### Ayarlar
- Maksimum hız
- Hız artış adımı
- Tanıma dili: Türkçe (`tr_TR`) veya İngilizce (`en_US`)

## Telsiz modülü
- **QR ile bağlanma:** Yer istasyonunun gösterdiği QR kodu okutulur (adres + token). Son bağlantı hatırlanır ve açılışta otomatik bağlanılır.
- **İki tanıma modu:**
  - *Yer STT:* Telefon ham sesi (16 kHz PCM16, 20 ms parçalar) akıtır. Tanıma yer istasyonunda yapılır. Basmadan önceki 300 ms ve bıraktıktan sonraki 150 ms de gönderilir, böylece kelime başı/sonu kesilmez.
  - *Telefon STT:* Telefon tanır, metni gönderir.
- **Konuşma kartları:** Her konuşma bir kartta izlenir: duyuldu → komut → yürütülüyor → tamamlandı / reddedildi / anlaşılmadı.
- **ACİL DUR düğmesi**
- **Telemetri şeridi:** PX4 telemetrisi, 2 Hz.
- **Sesli yanıt ve titreşim:** Ayarlardan açılıp kapatılır.
- **Otomatik yeniden bağlanma:** Bağlantı koparsa başlıkta "BAĞLANTI KOPTU" görünür ve istemci kendiliğinden yeniden bağlanır.
- **Ekranın kararmaması:** Uygulama açıkken ekran kapanmaz (wakelock).

## Simülasyona bağlanma
```bash
./start_bridge.sh   # rosbridge'i 9090 portunda başlatır, telefona girilecek IP'yi yazar
```
`rosbridge_server` kurulu değilse betik, mesajları `gz topic` ile Gazebo'ya ileten
hafif Python köprüsünü (`scripts/mobile_ws_bridge.py`) çalıştırır.

## Test
```bash
flutter analyze   # sorun yok
flutter test      # 49 test geçer, 1 test atlanır
```
