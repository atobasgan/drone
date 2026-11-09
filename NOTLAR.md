# NOTLAR

Çalışan sürümler, ölçümler ve görev durumu. Her fazın sonunda rakamları buraya
yaz (YOL_HARITASI.txt "Genel alışkanlıklar").

## Sürümler

`./scripts/surumleri_yaz.sh >> NOTLAR.md` çıktısını buraya ekle.

## Görev durumu (Faz 0–3)

Kod hazır = depoda; ✔ = birim testi / sahte simülasyonla doğrulandı;
**Makinede** = Ubuntu 26.04 + PX4 SITL üzerinde KONTROL maddeleri sen çalıştırınca işaretlenecek.

| Görev | Ne yapıldı | Durum |
|---|---|---|
| 0.1 Makine | `scripts/surumleri_yaz.sh` donanımı da yazar | Makinede |
| 0.2 ROS 2 Lyrical | `kurulum_faz0.sh ros` | Makinede |
| 0.3 Gazebo Jetty | `kurulum_faz0.sh gazebo` | Makinede |
| 0.4 PX4 SITL | `kurulum_faz0.sh px4` (B planı: `docker/Dockerfile` ROS_IMAGE) | Makinede |
| 0.5 XRCE köprüsü | `kurulum_faz0.sh agent workspace` | Makinede |
| 0.6 QGC + Ankara | `scripts/ortam.sh` PX4_HOME_* | Makinede |
| 0.7 Dondur | `.gitignore`, `hepsini_baslat.sh`, Docker, bu dosya | Kod hazır |
| 1.1 Offboard örneği | px4_ros_com `kurulum_faz0.sh workspace` ile gelir | Makinede (okuma) |
| 1.2 drone_interfaces | DroneCommand (+`mps`), CommandList (+zaman damgaları, `metin`, `kaynak`), Feedback | Kod hazır |
| 1.3 px4_interface | QoS BEST_EFFORT+TRANSIENT_LOCAL, `_v1` topic adlarını kendisi bulur, `konum_izleyici` | Kod hazır |
| 1.4 executor_node | 20 Hz akış, durum makinesi, kuyruk, dur/acil, feedback | ✔ sahte sim |
| 1.5 safety | YAML limitleri, liste benzetimi, pytest | ✔ 9 kural testi (geçen + kalan) |
| 1.6 Launch | `executor.launch.py`, `parser.launch.py`, `all.launch.py` | Kod hazır |
| 2.1 Normalizasyon | Türkçe I/İ, yazıyla sayı, ekli sayı ("elliye"), birimler, km→m | ✔ 49 örnek |
| 2.2 Hızlı yol | acil kelimeler + fullmatch kalıpları | ✔ 32 basit / 12 karmaşık, < 5 ms |
| 2.3 llama-server | `llama_cpp_kur.sh`, `model_indir.sh`, `llama_server.sh`, `llm_curl_test.sh` | ✔ bulutta (CPU) çalıştırıldı |
| 2.4 Prompt + şema | `schema.py`, `prompt.py` (few-shot), `llm_client.py`, `degerlendir.py`, 50 cümle | ✔ gerçek modelle baseline ölçüldü (aşağıda) |
| 2.5 parser_node | /voice/text → /drone/command, ısınma, zaman damgaları, önbellek | ✔ sahte sim |
| 3.1 Test kayıtları | `recordings/cumleler.jsonl` (107 cümle, tüm komut türleri, 12 negatif), `kayit_al` | Kayıt bekliyor (100+ WAV, 2-3 kişi) |
| 3.2 STT seçimi | `stt_karsilastir`: cümle %, komut %, ort/p95 ms, RTF, en sık yanlış duyulanlar | ✔ betik gerçek modelle denendi; ölçüm kayıt bekliyor |
| 3.3 stt_node | sounddevice + Silero VAD (400 ms) + faster-whisper, dosya modu, ısınma, uydurma filtresi | ✔ VAD/STT gerçek modelle, node sahte rclpy ile; mikrofon **Makinede** |
| 3.4 Uçtan uca ses | `all.launch.py` (stt dahil), `ses_test.launch.py`, `ses_testi` | Makinede |
| 3.5 latency_monitor | yürütücü t3/t4/t5 damgalar, `/latency/olcum` → CSV, `ozet` (ort/p50/p95, en yavaş aşama) | ✔ sahte sim + pytest; ölçüm **Makinede** |

## Tasarım kararları (MIMARI.txt'ten sapmalar / ayrıntılar)

- **Komut biçimi**: LLM ve hızlı yol MIMARI Bölüm 4'teki şemayı üretir (`kalk {irtifa_m}`).
  ROS mesajında `irtifa_m` → `metre` alanına konur; `hiz_ayarla` için `mps` alanı eklendi.
- **"bilinmiyor"**: Çok adımlı cevapta tek bir adım bile `bilinmiyor` ise hiçbir şey
  yapılmaz (temkinli).
- **Kuyruk**: Cümle "sonra / ardından" ile başlıyorsa kuyruğa eklenir; yoksa mevcut
  görev iptal edilip yenisi başlar. Kalkış sırasında gelen komut kalkışı iptal etmez,
  arkasına eklenir. "dur" her zaman her şeyi keser (iniş/eve dönüş dahil → offboard'da asılı kalır).
- **Güvenlik**: Liste, yürütülmeden önce baştan sona benzetilir; bir adım bile limiti
  aşarsa hiçbiri yürütülmez. Her adım başlarken gerçek konumla tekrar kontrol edilir.
- **hiz_ayarla**: PX4 offboard'da DO_CHANGE_SPEED'i uygulamadığı için setpoint hız×dt
  adımlarla taşınır (`hiz_mps`, 0 = PX4 limitleri).
- **llama-server**: `-c 2048` (Faz 2 few-shot prompt'u ~800 token), `-np 1`, `--jinja`;
  isteklerde `enable_thinking=false` ve `/no_think`.
- **Normalizasyon**: "2 km" → "2000 m" (LLM/hızlı yol tek birim görsün). "bir"/"yarım" yalnızca
  arkasından birim gelirse sayıdır ("bir şey" sayı değil). "ona git" sayı değil.

### Faz 3

- **Ses girişi ayrı topic**: `stt_node` → `/voice/stt` (`VoiceText`: metin + t0 + t1). `/voice/text`
  (String) terminal / telefon için aynen kalır; parser ikisini de dinler. Zaman damgaları String'e
  sığmadığı için böyle. "/voice/text'te görünüyor" kontrolü için `ros2 topic echo /voice/stt`.
- **Gecikme damgaları**: t0 = VAD konuşmanın bittiğine karar verdi (bitiş sessizliği beklendikten
  sonra; konuşmanın gerçek sonu t0 − `bitis_sessizlik_ms`). Dosya modunda t0 = dosya alındı.
  t3/t4/t5'i yürütücü ekler; t5 = hız vektörü 0.2 m/s değişti (`olcum_hiz_esigi_mps`).
  Kuyruğa eklenen / reddedilen komutta t4/t5 yok; `bekle` gibi hareketsiz komutta 5 sn sonra t5'siz kapanır.
- **Silero VAD 512 örnek** (32 ms) çerçeve ister; görevdeki 20-30 ms yerine bu kullanıldı.
- **Konuşma değil**: min 250 ms konuşma; Whisper'ın sessizlikte uydurduğu "Altyazı M.K." vb. ve
  `no_speech_prob` yüksek parçalar atılır. Mikrofon modunda boş sonuç yayınlanmaz.
- **STT ayarları**: `language="tr"`, `beam_size=1`, `temperature=0` (geri düşme denemesi yok),
  `initial_prompt` = drone sözlüğü (`stt_sozlugu.py`, 220 token, emir kipi; DRONE_SOZLUGU.txt),
  `condition_on_previous_text=False`.
- **Uydurma filtresi** (`stt.segmentleri_suz`): tekrar döngüsü (compression_ratio > 2.4) ve ses
  yokken sözlükten kopya (no_speech_prob > 0.5 + bütün kelimeler sözlükte) atılır; durdurma
  içeren metin hiç atılmaz.
- **Uzak makine** (Görev 3.3 son madde) yapılmadı: gerekirse `stt_node`'u mikrofonun olduğu makinede
  çalıştır; ağdan yalnızca `/voice/stt` metni gider.
- `kayit_klasoru` dolu ise her mikrofon konuşması WAV + duyulan metin olarak saklanır (Faz 4 verisi).

## Ölçümler

### Faz 2 baseline (Görev 2.4) — 2026-10-19

Ortam: bulut sunucusu, **GPU yok, 4 CPU çekirdeği**, llama.cpp (CPU), `-c 2048 -t 4`,
few-shot sistem prompt'u + JSON şema kısıtı. Gecikmeler kendi makinende (özellikle GPU ile)
çok daha düşük olacak; doğruluk rakamları donanımdan bağımsızdır.
Ham tablo: [NOTLAR_sonuclar.md](NOTLAR_sonuclar.md). Üretim hızı: 0.6B ≈ 36 token/sn (CPU).

| model | mod | tam eşleşme % | komut % | yanlış kabul % | LLM ort ms | LLM p95 ms |
|---|---|---|---|---|---|---|
| Qwen3 0.6B Q4_K_M | sadece_llm | 80.0 | 86.0 | 14.3 | ~1030 | ~1640 |
| Qwen3 0.6B Q4_K_M | tam_hat | 86.0 | 92.0 | 14.3 | ~1075 | ~1840 |
| Qwen3 1.7B Q4_K_M | sadece_llm | 84.0 | 88.0 | 0.0 | ~1970 | ~3480 |
| Qwen3 1.7B Q4_K_M | tam_hat | 90.0 | 94.0 | 0.0 | ~2185 | ~3830 |

"tam_hat" = normalize + acil + hızlı yol + LLM (50 cümlenin 22'si LLM'e hiç gitmedi).
Hızlı yol tek başına: tam eşleşme %58, yanlış kabul %0, < 0.1 ms.

Gözlemler (Faz 4 veri üretimi için):
- 0.6B alakasız cümleye komut uyduruyor ("saat kaç" -> bekle 60 sn): yanlış kabul %14.
  1.7B'de %0. Negatif örnekler veri setinde şart.
- İki modelde de ortak hatalar: "yüksekliği 200 m'ye ayarla" -> hiz_ayarla;
  "60 m irtifaya yüksel" göreli/mutlak karışıyor; "geri(ye)" -> alcal;
  çok adımda sayı bir sonraki adıma kayıyor ("sağa dön sonra 20 m" -> 20°).
- 0.6B sayıyı bozabiliyor ("50" -> 500). Normalizasyon doğru, hata modelde.
- Sonuç: fine-tune'suz hiçbir model %97 hedefine yakın değil -> Faz 4 gerekli.

### Faz 3 duman testi (sentetik ses) — 2026-11-04

Gerçek ölçüm DEĞİL: Mac M1 CPU, macOS'un Türkçe TTS sesi (Yelda) ile üretilmiş 20 WAV; amaç
betiklerin gerçek modellerle çalıştığını görmek. Gerçek tablo insan kayıtlarıyla (3.1) çıkarılacak.

| STT | cümle doğru % | komut tam % (yalnızca hızlı yol) | STT ort ms | RTF |
|---|---|---|---|---|
| base int8 | 35 | 20 | 296 | 0.23 |
| small int8 | 70 | 55 | 903 | 0.71 |

- Silero VAD: tıklama gürültüsü atıldı, sessizlikte STT boş döndü; 250 ms aralıklı iki komut
  (bitiş sessizliği 400 ms) tek parça oldu — beklenen davranış.
- Whisper büyük "İ" yerine "I" yazabiliyor ("Ileri" → normalize "ıleri"); gerçek kayıtlarda
  sık görülürse normalizasyona eklenmeli.
- Kısa komutlar ("sağa dön" → "Saadun") en çok bozulanlar; Faz 4 STT gürültüsü listesine.

### Drone sözlüğü (initial_prompt) — sentetik ses — 2026-11-09

Ayrıntı: DRONE_SOZLUGU.txt. Piper tr_TR-dfki, 167 cümle x 3 koşul (temiz / hızlı+gürültü SNR 8 /
telefon bandı) + 12 gürültü klibi; small int8, bulut CPU 4 çekirdek. Komut % = hızlı yol (LLM'siz).

| sözlük | token | cumleler.jsonl komut % | ayrı set komut % | kelime hatası % (cumleler) | gürültüden uydurma | STT ort ms |
|---|---|---|---|---|---|---|
| yok | 0 | 65.7 | 73.3 | 28.5 | 0/12 | 1410 |
| eski | 99 | 82.6 | 82.8 | 14.0 | 0/12 | 1452 |
| yeni | 220 | 93.1 | 91.1 | 9.4 | 0/12 (filtresiz 1/12 "Kalk.") | 1528 |

- Whisper Türkçe emirleri anlatıya çeviriyor ("yüksel" → "yükseldi", "git" → "gittik"); sözlüksüz 28 kez
  "meter". Emir kipindeki kısa cümleler ikisini de düzeltti.
- 223 token ≈ 540-580 Türkçe karakter (850 değil); fazlasının başı sessizce kesilir.
- Sonu "Kalk." olan sözlük gürültüden 11/12 "Kalk." uydurdu → sözlük "Acil dur. Dur." ile bitiyor.
- Gerçek kayıtlarla doğrulanmadı: `stt_karsilastir small:int8 --sozluk eski --sozluk yeni`.
