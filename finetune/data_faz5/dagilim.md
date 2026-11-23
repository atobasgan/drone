# Faz 5 veri dağılımı (Görev 5.4)

Üretim: `python3 -m finetune.data_gen.uret_harita`

Faz 4 verisi (`finetune/data/`) aynen alınır, üstüne `yere_git` örnekleri eklenir.

| bölüm | Faz 4 örnek | yeni örnek | yere_git tek | yere_git çok adımlı | kesmesiz (STT) | negatif | toplam |
|---|---|---|---|---|---|---|---|
| train | 3966 | 663 | 479 | 165 | 89 | 19 | 4629 |
| val | 717 | 88 | 62 | 24 | 13 | 2 | 805 |
| test | 791 | 173 | 122 | 45 | 39 | 6 | 964 |

## Yer adları (bölümler ayrık: testteki yerler eğitimde hiç geçmez)

- **train** (54): Abdi İpekçi Parkı, Ahlatlıbel, Altınpark, Ankara Garı, Ankara Kalesi, Ankara Üniversitesi, Anıtkabir, Atakule, Ayasofya, Aşti, Baraj Gölü, Batıkent, Bilkent, Botanik Parkı, Deniz Feneri, Dikmen Vadisi, Emirgan Korusu, Esenboğa Havalimanı, Etimesgut, Eymir Gölü, Fabrika, Futbol Sahası, Gazi Hastanesi, Gençlik Parkı, Hacettepe Hastanesi, Hacı Bayram Camii, Hamamönü, Harikalar Diyarı, Hükümet Konağı, Kadıköy İskelesi, Karşıyaka Çarşısı, Kemeraltı, Kocatepe Camii, Konak Meydanı, Kordon, Kurtuluş Parkı, Kuzguncuk, Kuğulu Park, Kültürpark, Kız Kulesi, Liman, Maçka Parkı, Otogar, Sakarya Caddesi, Su Deposu, Sıhhiye Köprüsü, Tandoğan, Tunalı Hilmi Caddesi, Ulus Heykeli, Ulus Meydanı, Çankaya Köşkü, Çayyolu, Şehir Hastanesi, Şehir Stadyumu
- **val** (13): Belediye Binası, Beypazarı, Dolmabahçe Sarayı, Galata Kulesi, Göksu Parkı, Keçiören, Kuğulu Göl, Kızılay Meydanı, Mogan Gölü, Orman Evi, Seğmenler Parkı, Taksim Meydanı, Tren İstasyonu
- **test** (17): Alsancak, Ankapark, Armada, Atatürk Orman Çiftliği, Belgrad Ormanı, Bostanlı, Cebeci Stadyumu, Gölbaşı, Kampüs, Kavaklıdere, Köy Meydanı, Merkez Camii, ODTÜ, Saat Kulesi, Spor Salonu, Sultanahmet Camii, Çamlıca Tepesi

## Atılan örnekler (otomatik kontrol)

| neden | adet |
|---|---|
| tekrar ya da baska bolumde var | 127 |
