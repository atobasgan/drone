# Faz 4 veri dağılımı

Üretim: `python3 -m finetune.data_gen.uret --tohum 42 --komut-basina 260 --ek-veri finetune/data/stt_ciktilari.jsonl`

| bölüm | örnek | tek adım | çok adımlı | negatif | STT gürültülü | ek veri |
|---|---|---|---|---|---|---|
| train | 3966 | 2762 | 705 | 499 | 368 | 248 |
| val | 717 | 479 | 135 | 103 | 85 | 0 |
| test | 791 | 543 | 152 | 96 | 83 | 0 |

## Komut dağılımı (adım sayısı)

| komut | train | val | test |
|---|---|---|---|
| alcal | 418 | 81 | 95 |
| bekle | 301 | 68 | 80 |
| bilinmiyor | 526 | 103 | 96 |
| don | 350 | 61 | 92 |
| dur | 144 | 15 | 13 |
| eve_don | 416 | 43 | 55 |
| git_koordinat | 177 | 53 | 47 |
| git_yon | 453 | 126 | 114 |
| hiz_ayarla | 302 | 22 | 47 |
| in | 327 | 29 | 26 |
| irtifaya_cik | 468 | 91 | 90 |
| kalk | 360 | 57 | 79 |
| yakin_yere_git | 173 | 42 | 57 |
| yuksel | 436 | 96 | 100 |

## Kaynak dağılımı (train)

| kaynak | örnek |
|---|---|
| sablon | 1284 |
| cesitleme | 1012 |
| cok_adim | 653 |
| ek_sablon | 270 |
| ek | 248 |
| negatif:sohbet | 159 |
| negatif:desteklenmeyen | 101 |
| negatif:yarim | 97 |
| negatif:eksik | 89 |
| negatif:ek | 53 |

## Atılan örnekler (otomatik kontrol)

| neden | adet |
|---|---|
| tekrar | 1820 |
| sayi cumlede yok | 231 |
| elle yazilmis test setinde var | 115 |
| baska bolumde var | 17 |
| etikette olmayan sayi | 13 |
| acil kelime var (LLM'e gitmez) | 3 |
