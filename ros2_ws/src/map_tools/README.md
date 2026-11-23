# Faz 5 — Harita komutları (`map_tools`)

"En yakın hastaneye git", "Anıtkabir'e git". Yol haritası: YOL_HARITASI.txt Faz 5,
kavramlar: KAVRAMLAR.txt Bölüm 9.

**Faz 0–4 koduna dokunulmadı.** Harita işi yeni bir düğümde yapılıyor; yürütücü ve
parser'ın mevcut fonksiyonları değişmedi, yeni davranış alt sınıflarla ve launch
dosyasındaki bir yönlendirmeyle (remap) ekleniyor.

## Akış

```
/voice/text ─> harita_parser_node ─/drone/command─> harita_node ─/drone/command_harita─> mission_executor
               (ParserNode alt sınıfı:              │ yakin_yere_git / yere_git var mı?
                + "en yakın X'e git" hızlı yolu      │   yok  -> liste AYNEN, beklemeden geçer
                + yere_git'i tanıyan LLM istemcisi)  │   var  -> konum (PX4) -> harita servisi
                                                     │          -> [irtifaya_cik 30 m, git_koordinat]
                                                     │   çok uzak / bulunamadı / hata -> red, drone kıpırdamaz
                                                     └─ /drone/feedback: "850 m uzaktaki Gazi Hastanesi için yola çıkıyorum"

/map/find_nearest (places_node)  aynı sağlayıcılarla tek başına servis (Görev 5.2)
```

Yürütücü `harita.launch.py`'de `SetRemap('/drone/command' -> '/drone/command_harita')` ile
başlar; kodu aynıdır. Harita komutunu hiç görmez, yalnızca `irtifaya_cik` ve `git_koordinat`
görür; güvenlik kontrolleri (mesafe, geofence, irtifa) her zamanki gibi orada yapılır.

## Dosyalar (her dosya tek iş)

| Dosya | Ne yapar |
|---|---|
| `map_tools/yer.py` | `Yer` (ad, enlem, boylam, mesafe, kaynak) ve `HaritaHatasi` |
| `map_tools/turler.py` | 8 yer türü → OSM etiketleri, Google tipleri, Türkçe ad (şemadaki `YER_TURLERI` ile aynı) |
| `map_tools/saglayici.py` | sağlayıcı arayüzü, `en_yakini_sec` (haversine), `json_iste` (zaman aşımı → `HaritaHatasi`) |
| `map_tools/osm.py` | ücretsiz: Overpass (en yakın tür), Nominatim (isimle arama) |
| `map_tools/google_places.py` | Google Places (New): Nearby Search, Text Search. Anahtar `GOOGLE_MAPS_API_KEY` |
| `map_tools/onbellek.py` | aynı sorgu (~50 m içinde) 10 dk tekrar servise gitmez; hata önbelleğe girmez |
| `map_tools/fabrika.py` | `saglayici_olustur('osm' \| 'google', zaman_asimi, onbellek_s)` |
| `map_tools/yer_cozucu.py` | **çekirdek, ROS'suz**: harita adımı → `[irtifaya_cik, git_koordinat]` ya da red sebebi |
| `map_tools/donustur.py` | ROS mesajı ↔ sözlük; zaman damgaları ve `kaynak` aynen taşınır (gecikme ölçümü bozulmaz) |
| `map_tools/harita_node.py` | ROS kabuğu: sıra, iptal, konum, geri bildirim |
| `map_tools/places_node.py` | `/map/find_nearest` servisi |
| `command_parser/harita_komutlari.py` | genişletilmiş şema (`yere_git`), `HaritaLLMIstemcisi`, `HaritaKomutCozucu` |
| `command_parser/harita_parser_node.py` | `HaritaParserNode(ParserNode)` |
| `drone_bringup/launch/harita.launch.py`, `config/harita.yaml` | hepsini birlikte başlatır |
| `araclar/sahte_sim/sim_harita.py` | ROS'suz uçtan uca deneme (sahte harita) |

## Komutlar

| Komut | Örnek | Ne olur |
|---|---|---|
| `yakin_yere_git {tur}` | "en yakın hastaneye git" | Faz 2'den beri şemada vardı, yürütücü reddediyordu. Artık hızlı yolla (LLM'siz, <5 ms) tanınır, `harita_node` en yakın yeri bulur |
| `yere_git {ad}` | "Anıtkabir'e git" | YENİ. LLM tanır (few-shot prompt'a bir satır + Faz 5 fine-tune'u), isimle aranır |

Türler: hastane, eczane, benzinlik, polis, itfaiye, okul, park, market.

## Kurallar

- **Görev 5.1 seyir:** harita hedefine gitmeden önce `seyir_irtifasi_m`'ye (30 m) çıkılır;
  drone zaten daha yüksekteyse alçalmaz. `git_koordinata_seyir: true` iken LLM'in kendi
  ürettiği `git_koordinat`'a da uygulanır. Drone yerdeyse örtük kalkış YOK; yürütücü
  her zamanki gibi "önce kalk" der.
- **Mesafe:** `en_uzak_m` (1000 m, `guvenlik.yaml` `max_adim_mesafe` ile aynı) ötesindeki
  yere gidilmez: "en yakın park 4.2 km uzakta; sınır 1.0 km".
- **Sıra:** Harita araması bitmeden gelen komut onu sollamaz ("en yakın parka git" + "sonra 5 m
  yüksel" doğru sırayla yürür). Harita komutu içermeyen liste, önünde bekleyen yoksa hemen geçer.
- **Dur:** "dur" ve `/drone/emergency_stop` beklemeden geçer ve bekleyen aramaları iptal eder;
  geç gelen arama sonucu yürütülmez ("dur geldi: bekleyen 1 harita komutu iptal edildi").
- **Konum:** PX4'ün yerel konumu + `ref_lat/ref_lon`'dan enlem/boylam. GPS yoksa
  `varsayilan_enlem/boylam` (Kızılay) ile aranır ve uyarı verilir.
- **Arama sürerken tırmanma yok** (Görev 5.3'te "cevap beklerken tırmanmaya başla" önerisi):
  KONTROL maddesi "sonuç yoksa drone hareket etmiyor" diyor, arama da genelde 1-2 sn sürüyor.
  Tırmanış, sonuç gelince listenin ilk adımı olarak yapılıyor.

## Çalıştırma (makinede)

```bash
./scripts/derle.sh                                           # yeni paket: map_tools
ros2 launch drone_bringup harita.launch.py                   # all.launch.py'nin harita'lı hali
ros2 launch drone_bringup harita.launch.py ft:=true          # Faz 5 fine-tune'lu model (aşağıda)
FT=1 ./scripts/harita_baslat.sh                              # tmux: sim + agent + llm + bu launch

# Google Places (Görev 5.4): anahtar koda / gite girmez
export GOOGLE_MAPS_API_KEY=...                               # Places API (New) açık olmalı
HARITA_YAML=$PWD/ros2_ws/install/drone_bringup/share/drone_bringup/config/harita_google.yaml ./scripts/harita_baslat.sh
```

### KONTROL maddeleri

```bash
# 5.2 servis (Ankara koordinatı -> gerçek hastane adı ve mantıklı mesafe)
ros2 service call /map/find_nearest drone_interfaces/srv/FindNearest \
    "{tur: hastane, enlem: 39.9208, boylam: 32.8541, yaricap_m: 3000.0}"
ros2 service call /map/find_nearest drone_interfaces/srv/FindNearest "{ad: 'Anıtkabir', enlem: 39.92, boylam: 32.85}"

# 5.1 koordinat (QGC'den bir nokta seç)
./scripts/komut_gonder.sh "{komut: 'kalk', metre: 10.0}"
./scripts/komut_gonder.sh "{komut: 'git_koordinat', enlem: 39.9240, boylam: 32.8590}"

# 5.3 / 5.4 cümleyle (sesle: konuşman yeterli)
./scripts/metin_gonder.sh "en yakın hastaneye git"
./scripts/metin_gonder.sh "Anıtkabir'e git"
ros2 topic echo /drone/feedback
```

## ROS'suz denemeler

```bash
python3 araclar/sahte_sim/sim_harita.py        # parser + harita_node + yürütücü, sahte harita
(cd ros2_ws/src/map_tools && python3 -m pytest -q)
./scripts/testleri_calistir.sh                 # hepsi (Faz 0-4 dahil)
```

`sim_harita.py` şunları dener: hızlı yol → önce 30 m'ye tırmanış, sonra hastaneye varış;
bekleyen aramayı sollamayan "sonra" komutu; arama sürerken "dur"; 1.9 km uzaktaki yerin reddi;
bulunamayan tür; isimle `yere_git`; harita dışı komutun beklemeden geçmesi; ACİL DUR.

## Görev 5.4 — veri ve fine-tune

```bash
python3 -m finetune.data_gen.uret_harita --dogrula        # -> finetune/data_faz5/ (Faz 4 verisi + yere_git)
python3 -m finetune.train.egit --ad drone-0.6b-faz5 --veri finetune/data_faz5
finetune/train/disa_aktar.sh drone-0.6b-faz5               # GGUF; parser_ft.yaml / FT_MODEL'i buna çevir
python3 -m finetune.eval.olc_harita --etiket drone-0.6b-faz5 --kisa-prompt   # llama-server açıkken
# llama.cpp yoksa: python3 -m finetune.eval.hf_sunucu --ad drone-0.6b-faz5 &  (aynı API, transformers)
```

- `finetune/data/` ve Faz 4'ün `uret.py`'si DEĞİŞMEDİ; Faz 4 verisi aynen alınıp üstüne eklendi,
  böylece eski test setinde gerileme ölçülebiliyor.
- Etiket kuralı: `ad` = cümledeki yer adının yalın hali ("kızılay meydanı'na uç" → `kızılay meydanı`).
  Testteki yer adları eğitimde hiç geçmiyor: model ezber değil kopyalamayı öğrenmeli.
- Sonuçlar: `finetune/eval/sonuclar_faz5.md` ve NOTLAR.md.

## Bu depoda doğrulanamayanlar

Bulut ortamında harita servislerine (Overpass, Nominatim, Google) canlı istek izin
denetiminde reddedildi; sağlayıcılar sahte HTTP cevaplarıyla test edildi. Gerçek bir
hastane adı ve mesafesi için yukarıdaki `ros2 service call` komutlarını kendi makinende
çalıştır. Google için `GOOGLE_MAPS_API_KEY` ve Google Cloud'da kota/bütçe uyarısı gerekir.
