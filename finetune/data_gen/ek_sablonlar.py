"""Gorev 4.6 ikinci tur: ilk modelin hata TURLERINE gore eklenen kaliplar. YALNIZ train'e girer.

Ilk fine-tune'lu modelin sentetik testteki hatalari (finetune/eval/hatalar/) dort ture ayrildi.
Test cumlelerinin kendisi EKLENMEDI; ayni turden YENI kaliplar yazildi (YOL_HARITASI 4.6).
Bu kaliplar sablonlari_bol'daki karistirmaya girmez: test ve val bolumleri birebir ayni kalir,
boylece iki model ayni test setinde karsilastirilabilir.

  1. goreli_mutlak  : "10 m in" -> irtifaya_cik dedi (dogrusu alcal). "X metre in" goreli,
                      "X metreye in" mutlak; ikisinin farki daha cok ornekle ogretilir.
  2. komutu_kacirdi : "eve git", fiilsiz "enlem X boylam Y" -> bilinmiyor dedi.
  3. negatifi_kabul : fiilsiz "50 m" -> yuksel, "en yakın yere git" -> polis, "güneye uç" -> 100 m
                      uydurdu. Sayi ya da yer soylenmemisse bilinmiyor.
  4. adim_sayisi    : "kalkıp 60 saniye bekle" -> kalk irtifa 60: ikinci adimin sayisini kalk'a
                      yapistirdi. Bu tur uret.py'de cok adimli orneklerin ilk adimi kalk/don/in
                      olacak sekilde agirliklandirilarak eklenir (--ilk-adim-orani).
"""

EK_SABLONLAR = {
    'alcal': [
        '{metre} metre daha in', '{metre} metre kadar in', '{metre} metre aşağı doğru in',
        'şimdi {metre} metre in', '{metre} metre in bakalım', 'bulunduğun yerden {metre} metre in',
        '{metre} metre aşağıya doğru alçal', 'olduğun yerden {metre} metre aşağı in',
    ],
    'yuksel': [
        '{metre} metre daha çık', '{metre} metre kadar çık', 'şimdi {metre} metre çık',
        'bulunduğun yerden {metre} metre yüksel', '{metre} metre yukarıya doğru çık',
    ],
    'irtifaya_cik': [
        '{irtifa} metreye kadar in', '{irtifa} metreye kadar çık', 'irtifayı {irtifa} metreye indir',
        '{irtifa} metre yüksekliğe in', 'yerden {irtifa} metreye çık', 'yerden {irtifa} metre yükseğe çık',
    ],
    'eve_don': [
        'eve uç', 'eve doğru git', 'evine git', 'eve geri git', 'hadi eve uç', 'eve doğru uç',
        'eve gidebilirsin', 'şimdi eve uç', 'üsse git', 'kalkış noktasına git',
    ],
    'git_koordinat': [
        'enlem {enlem} ve boylam {boylam}', 'konum enlem {enlem} boylam {boylam}',
        'hedef enlem {enlem} boylam {boylam}', '{enlem} enlemi {boylam} boylamı',
        'enlemi {enlem} boylamı {boylam} olan yere git', 'koordinatlar enlem {enlem} boylam {boylam}',
    ],
}

# Sayi, yon ya da yer eksik -> bilinmiyor. (Test bolumundeki cumlelerle ayni degil.)
EK_NEGATIFLER = [
    '30 m', 'yüz metre', 'yirmi metre hadi', 'tamam 100 metre', '70 metre lütfen', 'şimdi 40 metre',
    'iki yüz metre', '15 metre', 'otuz derece', 'kırk saniye', '5 metre bölü saniye',
    'doğuya uç', 'batıya uç hadi', 'kuzeye uç', 'sağa uç', 'ileri uç', 'geri uç', 'kuzeye doğru git',
    'güneye doğru uç', 'doğu tarafına git', 'batı yönüne uç', 'sola doğru uç',
    'en yakın yere uç', 'en yakın noktaya git', 'yakın bir yere git', 'en yakın yere götür',
    'en yakın binaya git', 'yakındaki bir yere uç', 'en yakın konuma git',
]
