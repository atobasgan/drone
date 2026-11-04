# Türkçe Sesli Komutla Drone Kontrolü

Gazebo Jetty + ROS 2 Lyrical + PX4 (SITL) + yerel küçük LLM.

| Belge | İçerik |
|---|---|
| [MIMARI.txt](MIMARI.txt) | ne ve neden: mimari, model seçimi, komut şeması |
| [YOL_HARITASI.txt](YOL_HARITASI.txt) | hangi sırayla: fazlar ve görev listesi |
| [KAVRAMLAR.txt](KAVRAMLAR.txt) | gereken kavramlar |
| [LLM_API_SENARYOSU.txt](LLM_API_SENARYOSU.txt) | LLM bize hazır verilirse: API + few-shot ile Faz 2 |
| [NOTLAR.md](NOTLAR.md) | sürümler, ölçümler, görev durumu |

## Durum

**Faz 0–3 kodu hazır** (kurulum betikleri, `drone_interfaces`, `mission_executor`,
`command_parser`, `voice_input`, `latency_monitor`, `drone_bringup`). Faz 3'te kayıtların
alınması ve ölçümler sırada; Faz 4 (veri + fine-tune) sonra. Hangi görevin makinede
doğrulanması gerektiği [NOTLAR.md](NOTLAR.md)'de.

## Akış

```
mikrofon ─> stt_node (VAD + STT) ─/voice/stt (VoiceText: metin + t0, t1)─┐
                                                                        v
/voice/text (String) ──> command_parser ──/drone/command (CommandList)──> mission_executor ──/fmu/in/*──> PX4
                         normalize                                       safety (limitler)
                         acil kelime ("dur")                             durum makinesi (20 Hz)
                         hızlı yol (regex, <5 ms)                        <──/fmu/out/*── PX4
                         LLM (llama-server, JSON şema)  /drone/feedback <──
                                                         /latency/olcum (t0..t5) ──> latency_monitor ──> CSV
```

## Klasörler

```
scripts/                   kurulum, derleme, başlatma, LLM betikleri
docker/                    Dockerfile + docker-compose (sim, agent, llm, dev)
ros2_ws/src/
  drone_interfaces/        DroneCommand, CommandList, Feedback mesajları
  mission_executor/        px4_interface.py, safety.py, planlayici.py, geo.py, executor_node.py
  command_parser/          normalize.py, fast_path.py, schema.py, prompt.py, llm_client.py, parser_node.py
  voice_input/             vad.py, stt.py, stt_node.py, kayit_al.py, stt_karsilastir.py, ses_testi.py
  latency_monitor/         monitor_node.py (CSV), ozet.py (ort / p50 / p95)
  drone_bringup/           launch/ + config/guvenlik.yaml, config/parser.yaml
recordings/                cumleler.jsonl (okunacak 107 cümle), *.wav + etiketler.csv
araclar/sahte_sim/         ROS'suz uçtan uca test (sahte rclpy + basit araç modeli)
```

## Kurulum (Faz 0)

```bash
./scripts/kurulum_faz0.sh                 # ROS 2, Gazebo, PX4, XRCE Agent, ros2_ws
# ya da adım adım: ./scripts/kurulum_faz0.sh ros gazebo px4 agent workspace
./scripts/surumleri_yaz.sh >> NOTLAR.md   # çalışan sürümleri dondur
```

PX4 sürümünü ve px4_msgs dalını eşleştir: `PX4_VERSION=release/1.16 ./scripts/kurulum_faz0.sh px4 workspace`.
Alternatif: `docker compose -f docker/docker-compose.yml build`.

## Faz 1 — terminalden JSON ile uçuş

```bash
./scripts/hepsini_baslat.sh faz1          # tmux: PX4+Gazebo, Agent, executor
# başka terminalde:
ros2 run mission_executor konum_izleyici  # Görev 1.3: konum/durum
./scripts/komut_gonder.sh "{komut: 'kalk', metre: 10.0}"
./scripts/komut_gonder.sh "{komut: 'yuksel', metre: 50.0}"
./scripts/komut_gonder.sh "{komut: 'don', yon: 'sag', derece: 90.0}" "{komut: 'git_yon', yon: 'ileri', metre: 20.0}"
./scripts/komut_gonder.sh "{komut: 'dur'}"
ros2 topic pub --once /drone/emergency_stop std_msgs/msg/Empty
ros2 topic echo /drone/feedback
```

Limitler `ros2_ws/src/drone_bringup/config/guvenlik.yaml`'da.

## Faz 2 — yazılı Türkçe cümleyle uçuş

```bash
./scripts/llama_cpp_kur.sh && ./scripts/model_indir.sh   # Qwen3 0.6B / 1.7B, GGUF Q4_K_M
./scripts/hepsini_baslat.sh                              # + llama-server + parser
./scripts/llm_curl_test.sh "500 m yüksel"                # sunucu cevap veriyor mu
./scripts/metin_gonder.sh "önce 20 metre yüksel sonra kuzeye 50 metre git"

# Baseline (Görev 2.4): 50 cümlelik test setinde doğruluk ve gecikme
ros2 run command_parser degerlendir --etiket qwen3-0.6b --tablo NOTLAR_sonuclar.md
ros2 run command_parser degerlendir --etiket qwen3-0.6b --sadece-llm --tablo NOTLAR_sonuclar.md
```

`llama-server` kapalıysa parser yalnızca hızlı yolla çalışmaya devam eder.

## Faz 3 — konuşarak uçuş

```bash
./scripts/ses_kur.sh                      # PortAudio, faster-whisper, Silero VAD, sounddevice
./scripts/derle.sh

# 3.1 Test kayıtları (ROS gerekmez; her konuşmacı 107 cümle, kaldığı yerden devam eder)
ros2 run voice_input kayit_al --konusmaci atakan        # depo kökünde çalıştır
# ROS'suz bir bilgisayarda (pip: numpy sounddevice):
PYTHONPATH=ros2_ws/src/voice_input:ros2_ws/src/command_parser python3 -m voice_input.kayit_al --konusmaci atakan

# 3.2 STT adaylarını ölç (ROS gerekmez) -> tablo + en sık yanlış duyulan kelimeler
ros2 run voice_input stt_karsilastir small:int8 medium:int8 --tablo NOTLAR_sonuclar.md --etiket "CPU 4c"
ros2 run voice_input stt_karsilastir large-v3-turbo:float16@cuda --llm http://127.0.0.1:8080

# 3.3 / 3.4 Mikrofonla uç (stt_node, all.launch.py içinde)
./scripts/hepsini_baslat.sh
ros2 topic echo /voice/stt                # "on metre yüksel" -> metin + zaman damgaları

# 3.4 Kayıtlı 100+ dosyayla uçtan uca doğruluk (drone uçmaz)
ros2 launch drone_bringup ses_test.launch.py
ros2 run voice_input ses_testi --etiket "small int8 + qwen3-1.7b" --tablo NOTLAR_sonuclar.md

# 3.5 Aşama aşama gecikme (latency_monitor her komutu ~/llm_drone_gecikme/*.csv'ye yazar)
ros2 launch drone_bringup all.launch.py stt_mod:=ikisi   # yürütücü açık: t4, t5 de ölçülür
ros2 run voice_input ses_testi --ara 3
ros2 run latency_monitor ozet ~/llm_drone_gecikme/gecikme_*.csv --tablo NOTLAR_sonuclar.md
```

STT / VAD ayarları `ros2_ws/src/drone_bringup/config/ses.yaml`'da.

## Testler (ROS gerektirmez)

```bash
pip install pytest requests
./scripts/testleri_calistir.sh
```
