# Faz 4 — Veri ve fine-tune

Hazır Qwen3 modelini kendi örneklerimizle (LoRA) eğitip "Türkçe drone cümlesi →
JSON" işine özelleştiriyoruz. Kazanç: kısa prompt (800 yerine ~30 token), daha
az uydurma ve STT hatalarına dayanıklılık. Kavramlar: KAVRAMLAR.txt Bölüm 8,
MIMARI.txt Bölüm 6-7, görevler: YOL_HARITASI.txt Faz 4.

## Klasörler (her dosya tek iş yapar)

```
finetune/
├── ortak.py                 yollar, chat-JSONL biçimi; sistem prompt'u command_parser'dan ALIR
├── data_gen/                Görev 4.1 - 4.3: veri üretimi
│   ├── parametreler.py      rastgele sayı/yön/yer + sayıyı yazıyla yazma ("yüz elli")
│   ├── sablonlar.py         4.1: her komut için 8-21 temel söyleyiş
│   ├── cesitleme.py         4.2: günlük, devrik, kibar, dolgulu söyleyişler
│   ├── negatifler.py        4.3: "bilinmiyor" örnekleri (sohbet, eksik sayı, yarım cümle...)
│   ├── stt_gurultusu.py     4.3: Whisper'ın gerçek hataları ("sağ dön", "ilerli", "meter")
│   ├── doldur.py            şablon + rastgele değer -> (cümle, etiket); etiketi kod kurar
│   ├── kontrol.py           her örneğin otomatik kontrolü (şema, sayı cümlede mi, acil kelime)
│   ├── uret.py              hepsini birleştirir -> data/train|val|test.jsonl + dagilim.md
│   ├── dogrula.py           üretilmiş veriyi denetler, gözle kontrol için örnek basar
│   ├── stt_ciktisi.py       4.3: cümle -> Piper -> Whisper -> gerçek STT çıktısı (ek veri)
│   ├── ek_sablonlar.py      4.6 ikinci tur: ilk modelin hata türlerine göre yeni kalıplar (yalnız train)
│   └── llm_cesitle.py       4.2 (isteğe bağlı): bir LLM'den yeni söyleyiş iste, doğrula
├── data/                    üretilen veri (git'te; aynı komutla birebir aynısı üretilir)
│                            train/val/test.jsonl, dagilim.md, stt_ciktilari.jsonl
├── train/                   Görev 4.5
│   ├── veri.py              chat -> token; kayıp yalnız cevapta; prompt llama-server'la aynı
│   ├── egit.py              LoRA eğitimi (transformers + peft; CPU ya da GPU)
│   ├── dene.py              birkaç cümleyi elle dene
│   ├── birlestir.py         LoRA + taban model -> tek model
│   └── disa_aktar.sh        -> GGUF f16 -> Q4_K_M ve Q8_0
├── eval/                    Görev 4.4, 4.6
│   ├── olc.py               bir modeli iki test setinde ölç -> sonuclar.md
│   ├── hata_turleri.py      hataları türlere ayır (göreli/mutlak, sayı, negatifi kabul...)
│   ├── model_olc.sh         GGUF'u llama-server'da aç, ölç, kapat
│   ├── sonuclar.md          sonuç tablosu
│   └── hatalar/             her model ve set için yanlış örnekler (okumak için)
└── models/                  eğitilmiş modeller (git'te DEĞİL: *.gguf, *.safetensors)
```

## Baştan sona çalıştırma (depo kökünden)

```bash
pip install torch transformers peft accelerate      # eğitim için (bir kez)

# 4.1-4.3 veri
python3 -m finetune.data_gen.uret                   # -> finetune/data/*.jsonl, dagilim.md
python3 -m finetune.data_gen.dogrula --ornek 50     # kontroller + gözle bakmak için 50 örnek
python3 -m finetune.data_gen.stt_ciktisi --adet 400 # (isteğe bağlı) gerçek Whisper çıktıları
python3 -m finetune.data_gen.uret --ek-veri finetune/data/stt_ciktilari.jsonl

# 4.4 baseline (fine-tune'suz, Faz 2'nin few-shot prompt'u)
THREADS=4 finetune/eval/model_olc.sh models/qwen3-0.6b-q4_k_m.gguf "qwen3-0.6b" hayir Q4_K_M --set sentetik
THREADS=4 finetune/eval/model_olc.sh models/qwen3-0.6b-q4_k_m.gguf "qwen3-0.6b" hayir Q4_K_M --set cumleler --tam-hat

# 4.5 eğitim -> dene -> GGUF
python3 -m finetune.train.egit                      # Qwen/Qwen3-0.6B, 2 epoch
python3 -m finetune.train.dene                      # birkaç cümleyi elle dene
finetune/train/disa_aktar.sh drone-0.6b             # -> finetune/models/drone-0.6b/*.gguf

# 4.6 değerlendir (kısa prompt!)
for Q in q4_k_m:Q4_K_M q8_0:Q8_0; do
  CTX=1024 THREADS=4 finetune/eval/model_olc.sh finetune/models/drone-0.6b/drone-0.6b-${Q%%:*}.gguf \
      "drone-0.6b" evet ${Q##*:} --kisa-prompt --set sentetik
  CTX=1024 THREADS=4 finetune/eval/model_olc.sh finetune/models/drone-0.6b/drone-0.6b-${Q%%:*}.gguf \
      "drone-0.6b" evet ${Q##*:} --kisa-prompt --set cumleler --tam-hat
done
# hataları oku: finetune/eval/hatalar/ ; en sık hata türü için data_gen/ek_sablonlar.py'ye
# AYNI TÜRDEN yeni kalıp ekle (test cümlesini değil) -> uret -> egit -> yeniden ölç

# 4.7 uçtan uca: cümleleri seslendir -> Whisper -> hızlı yol + LLM
PYTHONPATH=ros2_ws/src/voice_input:ros2_ws/src/command_parser python3 -m voice_input.sentetik_set \
    recordings/cumleler.jsonl --cikti /tmp/e2e --ses ~/piper/tr_TR-dfki-medium.onnx
PYTHONPATH=ros2_ws/src/voice_input:ros2_ws/src/command_parser python3 -m voice_input.stt_karsilastir \
    small:int8 --etiketler /tmp/e2e/etiketler.csv --llm http://127.0.0.1:8080 --kisa-prompt

# 4.7 devreye al
FT=1 ./scripts/hepsini_baslat.sh                    # fine-tune'lu GGUF (FT_MODEL) + parser_ft.yaml
```

GPU'n varsa `egit.py` aynen çalışır (bf16, çok daha hızlı). Colab/Kaggle'da:
depoyu klonla, `pip install peft`, `python3 -m finetune.train.egit`, `finetune/models/`
klasörünü indir.

## Önemli kararlar ve nedenleri

**1. Eğitim girdisi = `normalize()` çıktısı.** Kullanımda LLM'e "beş yüz metre
yüksel" değil "500 m yüksel" gider (komut_cozucu önce normalize eder). Model
eğitimde de aynı biçimi görür. Sayıyı çevirmek LLM'in değil normalize'ın işi.

**2. Prompt birebir aynı.** Sistem prompt'u (`KISA_SISTEM_PROMPT`) `command_parser/prompt.py`'den
okunur, kopyalanmaz. Qwen3'te düşünme kapalıyken asistan cevabı boş bir
`<think></think>` ile başlar; `train/veri.py` prompt'u aynı sohbet şablonuyla
(`enable_thinking=False`) kurar. Eğitimde gördüğü metin ile llama-server'ın verdiği
metin aynıdır.

**3. Şablon bazında bölme.** Bir şablondan ("{metre} metre tırman") türeyen bütün
cümleler aynı bölüme düşer. Test seti, eğitimde hiç görülmemiş söyleyiş
kalıplarından oluşur; ezber ölçülmez.

**4. Elle yazılmış test cümleleri eğitime hiç girmez.** `recordings/cumleler.jsonl`
(107 cümle) üretilen veriden otomatik çıkarılır (`ortak.el_yazisi_cumleler`). Bu set
bizim yazmadığımız bir "dış" test olarak kalır.

**5. Etiketi hep kod kurar.** Şablon da LLM çeşitlemesi de yalnızca cümleyi verir;
sayı ve yön, cümleye yazılan rastgele değerden gelir. `kontrol.py` her sayının
normalize edilmiş cümlede aynen geçtiğini denetler; geçmeyen örnek atılır.

**6. "dur" geçen cümleler.** Hızlı yolun acil kuralı "dur / iptal / acil / stop"
geçen her cümleyi LLM'e uğramadan durdurur. Bu yüzden "kalk ve 20 m'de dur" gibi
cümleler eğitimde yok: LLM onları hiç görmeyecek.

**7. Eksik sayı = bilinmiyor.** "yüksel", "kuzeye git" (sayı yok) → `bilinmiyor`.
Model sayı uydurmamalı. Tek istisna: derecesi söylenmeyen dönüş 90° (elle yazılmış
test setindeki kural).

## Bu fazda ayrıca düzeltilenler

Veri üretirken ve gözle kontrol ederken bulunan, canlı sistemi de etkileyen hatalar:

| Ne | Önce | Sonra |
|---|---|---|
| `normalize("ondan sonra 10 m alçal")` | `10'dan sonra ...`: kuyruk bağlacı hiç tanınmıyordu | `ondan sonra ...` |
| `normalize("50 meter")` (Whisper'ın en sık hatası) | `50 meter`: birim tanınmıyordu | `50 m` |
| `normalize("bir elli metre")` ("bi elli") | `51 m` | `bir 50 m` |
| `normalize("1 dakika bekle")` | dakika LLM'e kalıyordu | `60 saniye bekle` (hızlı yol çözer) |
| `normalize("36 km/saat")` | `36000 m saat` | `10 m s` (hızlı yol çözer) |
| hızlı yol `hızını 5 m s yap` | eşleşmiyordu | `hiz_ayarla 5` |
| `llm_max_tokens` | 64: 3 adımlı koordinat cevabı (88 token) yarıda kesiliyordu | 128 |

## Sonuçlar

Ortam: bulut makinesi, **GPU yok, 4 CPU çekirdeği**, llama.cpp `-t 4`. Doğruluk donanımdan
bağımsızdır; süreler GPU'lu makinede çok daha kısa olur. Ham tablo: [eval/sonuclar.md](eval/sonuclar.md),
yanlış örnekler: [eval/hatalar/](eval/hatalar/).

İki test seti:
- **sentetik** (791): `data/test.jsonl`. Eğitimde hiç görülmemiş şablonlardan ve negatif
  cümlelerden üretildi; %10'u STT gürültülü.
- **cumleler** (107): `recordings/cumleler.jsonl`. Elle yazılmış, eğitime hiç girmedi.
  "Dış" test bu; asıl karar bu sete göre verilir.

"sadece LLM" = hızlı yol kapalı, modelin kendisi. "tam hat" = normalize + acil + hızlı yol + LLM
(canlı sistem).

| model | fine-tune | quant | prompt | sentetik tam % | sentetik yanlış kabul % | cumleler tam % (sadece LLM) | cumleler tam % (tam hat) | LLM ort ms |
|---|---|---|---|---|---|---|---|---|
| Qwen3 0.6B | hayır | Q4_K_M | few-shot (~800 token) | 52.8 | 60.4 | 77.6 | 88.8 | 1390 |
| Qwen3 1.7B | hayır | Q4_K_M | few-shot | 69.0 | 52.1 | 87.9 | 94.4 | 2289 |
| drone-0.6b tur 1 | evet | Q4_K_M | kısa (~30 token) | 88.9 | 11.5 | 98.1 | 98.1 | 688 |
| drone-0.6b tur 1 | evet | Q8_0 | kısa | 90.8 | 10.4 | 97.2 | 97.2 | 543 |
| drone-0.6b tur 2 | evet | Q4_K_M | kısa | 93.6 | 2.1 | **99.1** | **99.1** | 684 |
| **drone-0.6b tur 2** | evet | **Q8_0** | kısa | **94.3** | **0.0** | **99.1** | **99.1** | **526** |

Yol haritasının hedefi (tam eşleşme > %97, yanlış kabul < %1): elle yazılmış sette
**%99.1 / %0** ile sağlandı. Sentetik sette %94.3 / %0; bu set bilerek eğitimde hiç
görülmemiş söyleyiş kalıplarından oluşuyor, yani en zor ölçüt.

**Seçilen: drone-0.6b tur 2, Q8_0** (`scripts/ortam.sh` FT_MODEL). Q4 ile doğruluk neredeyse
aynı; Q8 yanlış kabulde (en tehlikeli hata) biraz daha iyi ve bu CPU'da daha hızlı.

**Uçtan uca (Görev 4.7):** Aynı 321 sesli klip (107 cümle × 3 koşul, Piper) → Whisper small
→ normalize → hızlı yol + LLM. STT aynı olduğu için fark yalnızca LLM'den geliyor:

| LLM | STT cümle doğru % | komut tam doğru % | komut türü doğru % |
|---|---|---|---|
| Qwen3 0.6B, few-shot | 67.3 | 78.5 | 85.7 |
| drone-0.6b tur 2, kısa prompt | 67.3 | **86.6** | **89.1** |

Fine-tune'lu model, Whisper'ın bozduğu cümleleri de daha iyi anlıyor (eğitimdeki STT
gürültüsü). Kalan tavanı artık STT belirliyor.

### Ne öğrendik

- **Fine-tune'lu 0.6B, 3 kat büyük hazır 1.7B'yi her ölçütte geçiyor ve ondan 3 kat hızlı.**
  Kısa prompt (~30 token) sayesinde istek başına işlenen token sayısı 800'den 50'ye iniyor.
- **Yanlış kabul en büyük kazanç:** Hazır modeller sayısı söylenmemiş "kuzeye git",
  "yüksel" gibi cümlelere sayı uyduruyor (%52-60). Fine-tune'lu model bunu büyük ölçüde
  bıraktı. Negatif örneklerin (%13) etkisi.
- **Q4 ile Q8 arasında doğruluk farkı gürültü düzeyinde.** Bu makinede Q8 daha hızlı
  çıktı (llama.cpp CPU'ya özel optimizasyonsuz derlendiğinde Q4_K'nın açılımı pahalı).
  GPU'da ya da `GGML_NATIVE=ON` derlemede kendi makinende ikisini ölç; küçük olanı (Q4) seç.
- **İlk turun hataları dört türdeydi** (`eval/hatalar/`): göreli/mutlak ("10 m in" →
  `irtifaya_cik`), komutu kaçırma ("eve git", fiilsiz koordinat), negatifi kabul ("50 m"),
  çok adımda sayının yanlış adıma yapışması ("kalkıp 60 saniye bekle" → `kalk irtifa 60`).
  İkinci turda bu türlerden **yeni** kalıplar eklendi (`data_gen/ek_sablonlar.py`, yalnız train'e;
  test ve val dosyaları md5 ile birebir aynı kaldı). Sonuç: göreli/mutlak 29→12, negatifi
  kabul 11→2, adım hatası 9→4, yanlış kabul %11.5→%2.1 (Q8'de %0).
- **Tekrar döngüsü:** Model nadiren "kalk, kalk, kalk, …" üretti. `llm_client.py` artık
  aynı adım 3+ kez art arda gelirse cevabı reddediyor (komut yerine "anlaşılmadı").
- **Kalan hatalar** birkaç görülmemiş kalıpta toplanıyor: "X m saniyeyle uç" (hız),
  "X m irtifa kazan" (yükselme) ve elle yazılmış setteki tek hata "kalk ve otuz metre ileri
  git" → `kalk irtifa 30`. Üçüncü tur için bu türlerden yeni kalıp eklenebilir; asıl
  sonraki adım gerçek ses kayıtlarıyla (Görev 3.1) yeniden ölçmek.

### Bilinen sınırlar

- Test sesleri ve "gerçek STT çıktıları" tek bir sentetik sesten (Piper) geliyor.
  Gerçek konuşmacı kayıtlarıyla (Görev 3.1) yeniden ölç.
- Eğitim bu makinede CPU'da ~2 saat sürdü (tur 1: 135 dk, tur 2: 126 dk; gradient
  checkpointing açık, tepe bellek ~7.7 GB). GPU'da (Colab T4) dakikalar sürer.
- Model dosyaları git'te değil (`.gitignore`: `models/`, `*.gguf`). Aynı veri ve tohumla
  `egit.py` + `disa_aktar.sh` aynı modeli üretir (CPU/GPU farkıyla küçük sayısal farklar olabilir).
- FunctionGemma 270M (Görev 4.6) Hugging Face'te lisans onayı istiyor. Hesabınla onayla,
  `huggingface-cli login`, sonra: `python3 -m finetune.train.egit --taban google/functiongemma-270m-it
  --ad drone-gemma`. Bu ortamda denenmedi.
- Qwen3 1.7B'nin fine-tune'u aynı betikle (`--taban Qwen/Qwen3-1.7B`) yapılır; CPU'da ~6 saat
  süreceği için GPU'da yapılmalı. 0.6B zaten 1.7B'yi geçtiği için öncelikli değil.
