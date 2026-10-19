# NOTLAR

Çalışan sürümler, ölçümler ve görev durumu. Her fazın sonunda rakamları buraya
yaz (YOL_HARITASI.txt "Genel alışkanlıklar").

## Sürümler

`./scripts/surumleri_yaz.sh >> NOTLAR.md` çıktısını buraya ekle.

## Görev durumu (Faz 0–2)

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
