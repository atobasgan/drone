# Türkçe Sesli Komutla Drone Kontrolü

Gazebo Jetty + ROS 2 Lyrical + PX4 (SITL) + yerel küçük LLM.

| Belge | İçerik |
|---|---|
| [MIMARI.txt](MIMARI.txt) | ne ve neden: mimari, model seçimi, komut şeması |
| [YOL_HARITASI.txt](YOL_HARITASI.txt) | hangi sırayla: fazlar ve görev listesi |
| [KAVRAMLAR.txt](KAVRAMLAR.txt) | gereken kavramlar |
| [NOTLAR.md](NOTLAR.md) | sürümler, ölçümler, görev durumu |

## Durum

**Faz 0–2 kodu hazır** (kurulum betikleri, `drone_interfaces`, `mission_executor`,
`command_parser`, `drone_bringup`). Faz 3 (ses) sırada. Hangi görevin makinede
doğrulanması gerektiği [NOTLAR.md](NOTLAR.md)'de.

## Akış

```
/voice/text (String) ──> command_parser ──/drone/command (CommandList)──> mission_executor ──/fmu/in/*──> PX4
                         normalize                                       safety (limitler)
                         acil kelime ("dur")                             durum makinesi (20 Hz)
                         hızlı yol (regex, <5 ms)                        <──/fmu/out/*── PX4
                         LLM (llama-server, JSON şema)  /drone/feedback <──
```

## Klasörler

```
scripts/                   kurulum, derleme, başlatma, LLM betikleri
docker/                    Dockerfile + docker-compose (sim, agent, llm, dev)
ros2_ws/src/
  drone_interfaces/        DroneCommand, CommandList, Feedback mesajları
  mission_executor/        px4_interface.py, safety.py, planlayici.py, geo.py, executor_node.py
  command_parser/          normalize.py, fast_path.py, schema.py, prompt.py, llm_client.py, parser_node.py
  drone_bringup/           launch/ + config/guvenlik.yaml, config/parser.yaml
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

## Testler (ROS gerektirmez)

```bash
pip install pytest requests
./scripts/testleri_calistir.sh
```
