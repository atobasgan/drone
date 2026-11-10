# Faz 4 sonuç tablosu

Üretim: `finetune/eval/model_olc.sh` (python3 -m finetune.eval.olc). Donanım etikette yazılı.

| tarih | model | fine-tune | quant | prompt | test seti | mod | n | tam eşleşme % | komut % | parametre % | yanlış kabul % | LLM ort ms | LLM p95 ms | hata türleri |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | qwen3-0.6b (CPU 4c) | hayir | Q4_K_M | few-shot | sentetik | sadece_llm | 791 | 52.8 | 62.6 | 83.2 | 60.4 | 1390 | 2530 | komut_yanlis 86, adim_sayisi 86, goreli_mutlak 65, yon 63, negatifi_kabul 58, sayi 14, komutu_kacirdi 1 |
| 2026-11-10 | qwen3-0.6b (CPU 4c) | hayir | Q4_K_M | few-shot | cumleler | sadece_llm | 107 | 77.6 | 86.0 | 88.8 | 0.0 | 1145 | 1774 | komut_yanlis 8, yon 6, adim_sayisi 6, sayi 3, goreli_mutlak 1 |
| 2026-11-10 | qwen3-0.6b (CPU 4c) | hayir | Q4_K_M | few-shot | cumleler | tam_hat | 107 | 88.8 | 93.5 | 94.3 | 0.0 | 1176 | 1955 | adim_sayisi 4, komut_yanlis 3, yon 3, sayi 2 |
| 2026-11-10 | drone-0.6b tur1 (CPU 4c) | evet | Q4_K_M | kısa | sentetik | sadece_llm | 791 | 88.9 | 89.0 | 99.8 | 11.5 | 688 | 1339 | goreli_mutlak 29, komutu_kacirdi 23, komut_yanlis 15, negatifi_kabul 11, adim_sayisi 9, sayi 1 |
| 2026-11-10 | drone-0.6b tur1 (CPU 4c) | evet | Q4_K_M | kısa | cumleler | sadece_llm | 107 | 98.1 | 99.1 | 98.9 | 0.0 | 608 | 1009 | adim_sayisi 1, sayi 1 |
| 2026-11-10 | drone-0.6b tur1 (CPU 4c) | evet | Q4_K_M | kısa | cumleler | tam_hat | 107 | 98.1 | 99.1 | 98.9 | 0.0 | 646 | 1240 | adim_sayisi 1, sayi 1 |
| 2026-11-10 | drone-0.6b tur1 (CPU 4c) | evet | Q8_0 | kısa | sentetik | sadece_llm | 791 | 90.8 | 90.9 | 99.8 | 10.4 | 543 | 1053 | komutu_kacirdi 25, goreli_mutlak 24, negatifi_kabul 10, komut_yanlis 7, adim_sayisi 6, sayi 1 |
| 2026-11-10 | drone-0.6b tur1 (CPU 4c) | evet | Q8_0 | kısa | cumleler | sadece_llm | 107 | 97.2 | 97.2 | 100.0 | 0.0 | 458 | 715 | adim_sayisi 2, komutu_kacirdi 1 |
| 2026-11-10 | drone-0.6b tur1 (CPU 4c) | evet | Q8_0 | kısa | cumleler | tam_hat | 107 | 97.2 | 97.2 | 100.0 | 0.0 | 454 | 852 | adim_sayisi 2, komutu_kacirdi 1 |
| 2026-11-10 | qwen3-1.7b (CPU 4c) | hayir | Q4_K_M | few-shot | sentetik | sadece_llm | 791 | 69.0 | 72.8 | 94.3 | 52.1 | 2289 | 4327 | goreli_mutlak 69, komut_yanlis 62, negatifi_kabul 50, adim_sayisi 32, sayi 16, yon 14, komutu_kacirdi 2 |
| 2026-11-10 | qwen3-1.7b (CPU 4c) | hayir | Q4_K_M | few-shot | cumleler | sadece_llm | 107 | 87.9 | 92.5 | 94.3 | 0.0 | 1927 | 3156 | komut_yanlis 4, sayi 4, goreli_mutlak 3, komutu_kacirdi 1, yon 1 |
| 2026-11-10 | qwen3-1.7b (CPU 4c) | hayir | Q4_K_M | few-shot | cumleler | tam_hat | 107 | 94.4 | 97.2 | 96.7 | 0.0 | 2098 | 3528 | komut_yanlis 3, sayi 3 |
| 2026-11-10 | drone-0.6b tur2 (CPU 4c) | evet | Q4_K_M | kısa | sentetik | sadece_llm | 791 | 93.6 | 93.9 | 99.5 | 2.1 | 684 | 1277 | komutu_kacirdi 16, komut_yanlis 14, goreli_mutlak 12, adim_sayisi 4, yon 3, negatifi_kabul 2 |
| 2026-11-10 | drone-0.6b tur2 (CPU 4c) | evet | Q4_K_M | kısa | cumleler | sadece_llm | 107 | 99.1 | 99.1 | 100.0 | 0.0 | 595 | 916 | adim_sayisi 1 |
| 2026-11-10 | drone-0.6b tur2 (CPU 4c) | evet | Q4_K_M | kısa | cumleler | tam_hat | 107 | 99.1 | 99.1 | 100.0 | 0.0 | 610 | 1011 | adim_sayisi 1 |
| 2026-11-10 | drone-0.6b tur2 (CPU 4c) | evet | Q8_0 | kısa | sentetik | sadece_llm | 791 | 94.3 | 94.6 | 99.7 | 0.0 | 526 | 983 | komutu_kacirdi 21, goreli_mutlak 18, adim_sayisi 3, yon 2, komut_yanlis 1 |
| 2026-11-10 | drone-0.6b tur2 (CPU 4c) | evet | Q8_0 | kısa | cumleler | sadece_llm | 107 | 99.1 | 99.1 | 100.0 | 0.0 | 451 | 707 | adim_sayisi 1 |
| 2026-11-10 | drone-0.6b tur2 (CPU 4c) | evet | Q8_0 | kısa | cumleler | tam_hat | 107 | 99.1 | 99.1 | 100.0 | 0.0 | 457 | 797 | adim_sayisi 1 |

## Uçtan uca (Görev 4.7): ses → Whisper → normalize → hızlı yol + LLM

`recordings/cumleler.jsonl`'ün 107 cümlesi Piper ile 3 koşulda seslendirildi (321 klip:
temiz / hızlı + gürültü / telefon bandı, `voice_input.sentetik_set`). STT: faster-whisper small
int8 + drone sözlüğü (Faz 3). Üretim: `voice_input.stt_karsilastir --llm ... [--kisa-prompt]`.

| tarih | LLM | n | STT cümle doğru % | komut tam % | komut türü % | STT ort ms |
|---|---|---|---|---|---|---|
| 2026-11-10 | qwen3-0.6b Q4_K_M, few-shot (CPU 4c) | 321 | 67.3 | 78.5 | 85.7 | 1412 |
| 2026-11-10 | drone-0.6b tur2 Q4_K_M, kısa prompt (CPU 4c) | 321 | 67.3 | 86.6 | 89.1 | 1427 |
