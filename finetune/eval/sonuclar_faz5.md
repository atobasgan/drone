# Faz 5 sonuç tablosu (Görev 5.4)

Üretim: `python3 -m finetune.eval.olc_harita`. "quant" sütunu arka ucu yazar (hf-fp32: transformers, şema kısıtı yok).

| tarih | model | fine-tune | quant | prompt | test seti | mod | n | tam eşleşme % | komut % | parametre % | yanlış kabul % | LLM ort ms | LLM p95 ms | hata türleri |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-23 | drone-0.6b-faz5 | evet | hf-fp32 | kısa | sentetik | sadece_llm | 791 | 95.7 | 95.7 | 100.0 | 0.0 | 3032 | 5567 | komut_yanlis 16, goreli_mutlak 7, komutu_kacirdi 7, adim_sayisi 4 |
| 2026-11-23 | drone-0.6b-faz5 | evet | hf-fp32 | kısa | cumleler | sadece_llm | 107 | 99.1 | 99.1 | 100.0 | 0.0 | 2688 | 4547 | adim_sayisi 1 |
| 2026-11-23 | drone-0.6b-faz5 | evet | hf-fp32 | kısa | harita | sadece_llm | 173 | 73.4 | 93.6 | 77.6 | 0.0 | 3018 | 4619 | yer_adi 35, komutu_kacirdi 9, adim_sayisi 2 |
