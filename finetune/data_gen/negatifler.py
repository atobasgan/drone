"""Gorev 4.3: negatif ornekler -> {"adimlar":[{"komut":"bilinmiyor"}]}.

Bunlar olmazsa model her cumleye bir komut uydurur. Faz 2 baseline'inda 0.6B
"saat kaç" cumlesine "60 saniye bekle" uretti (yanlis kabul %14).
Gruplar ayri tutulur ki dagilim raporunda hangisinin eksik oldugu gorulsun.
"""

NEGATIFLER = {
    # gundelik konusma, soru, sohbet
    'sohbet': [
        'bugün hava nasıl', 'yemek ne zaman', 'saat kaç', 'merhaba', 'nasılsın', 'günaydın',
        'iyi akşamlar', 'teşekkür ederim', 'bugün çok yoruldum', 'bu akşam maç var mı',
        'annem beni aradı mı', 'telefonum nerede', 'bana bir şarkı söyle', 'bir fıkra anlat',
        'adın ne', 'kaç yaşındasın', 'yarın yağmur yağacak mı', 'çay içelim mi',
        'kahve ister misin', 'hangi takımı tutuyorsun', 'bugün günlerden ne', 'saat kaçta buluşalım',
        'bu drone çok güzel olmuş', 'çok iyi uçuyorsun', 'aferin', 'harika', 'hadi bakalım',
        'tamam anladım', 'evet', 'hayır', 'belki', 'bilmiyorum', 'ne dedin', 'anlamadım',
        'bir daha söyler misin', 'sesimi duyuyor musun', 'test bir iki', 'deneme deneme',
        'alo', 'kim var orada', 'neredeyiz şu an', 'akşam ne yiyelim', 'markete gitmem lazım',
        'arabayı park ettim', 'okula geç kaldım', 'hastaneye randevu almam gerek',
        'eczane nöbetçi mi', 'kuzey kutbu çok soğuk', 'güneyde tatil yapalım',
        'ne yapıyorsun', 'beni duyuyor musun', 'çok güzel bir gün', 'hava çok rüzgarlı',
        'ankara kaç kilometre', 'yirmi yaşındayım', 'elli lira verdim', 'iki saat sonra görüşürüz',
        'üç kişiyiz', 'yüz metre koşusu kaç saniye', 'kuzeyden soğuk hava geliyor', 'sağ elim ağrıyor',
        'sol tarafta bir ağaç var', 'yukarıda bir kuş var', 'aşağıda insanlar var', 'bu ne',
        'bu kim', 'kaç metre yüksekteyiz', 'ne kadar uzaktayız', 'drone nereye gidiyor',
        'pilin bitmek üzere mi', 'bugün kaç derece', 'otuz derece sıcak var', 'eve gidince ararım',
        'yemekten sonra gelirim', 'önce kahvaltı yapalım', 'kalkmam lazım',
        'yarın erken kalkacağım', 'uçak kaçta iniyor', 'yere düşürdüm telefonu', 'havalar ısındı',
    ],
    # dronun yapamadigi ya da semada olmayan isler
    'desteklenmeyen': [
        'fotoğraf çek', 'video kaydet', 'kamerayı aç', 'ışıkları yak', 'takla at', 'dans et',
        'müzik çal', 'şarjın ne durumda', 'batarya yüzde kaç', 'kaç dakika uçabilirsin',
        'hızın ne kadar', 'yüksekliğin kaç metre', 'neredesin', 'konumunu söyle', 'paket bırak',
        'kargoyu teslim et', 'beni takip et', 'etrafı tara', 'haritayı göster', 'sesini aç',
        'ışıkları kapat', 'televizyonu aç', 'kapıyı kilitle', 'alarm kur', 'mesaj gönder',
        'zoom yap', 'yakınlaştır', 'kayda başla', 'kaydı durdurma', 'gimbalı aşağı çevir',
        'ters dön', 'şekil çiz', 'daire çiz', 'sekiz çiz', 'etrafında tur at', 'beni bul',
        'arabayı takip et', 'yüzümü tanı', 'sıcaklığı ölç', 'rüzgar hızını söyle', 'su püskürt',
        'ilaçlama yap', 'hoparlörden anons yap', 'ışığı yak', 'lazeri aç', 'görüntü gönder',
    ],
    # eksik parametre: sayi soylenmemis; uydurmak yerine bilinmiyor (temkinli)
    'eksik': [
        'yüksel', 'biraz yüksel', 'alçal', 'biraz alçal', 'ileri git', 'kuzeye git', 'biraz ileri',
        'geri git', 'sağa git', 'sola git', 'yukarı çık', 'aşağı in biraz', 'biraz yukarı',
        'irtifaya çık', 'metreye çık', 'hızını ayarla', 'hızlan', 'yavaşla', 'şuraya git',
        'oraya git', 'buraya gel', 'koordinata git', 'en yakın yere git', 'bir yere git',
        'metre yüksel', 'derece dön', 'saniye bekle', 'şu kadar yüksel', 'biraz daha',
        'daha yükseğe', 'daha alçağa', 'biraz doğuya', 'güneye uç', 'batıya doğru git', 'biraz geri gel',
        'yukarıya', 'aşağıya', 'irtifa artır', 'irtifayı azalt', 'yükseklik ayarla', 'hızını değiştir',
        'şu binaya git', 'ağacın yanına git', 'koordinatlara git', 'en yakına git',
    ],
    # yarim kalan cumleler ve STT'nin uydurmalari
    'yarim': [
        'şey', 'şey yani ee', 'ee', 'hmm', 'yani', 'şimdi', 'tamam şimdi', 'önce', 'sonra',
        've', 'kuzeye', 'elli metre', 'metre', 'iki yüz', 'sağa doğru', 'en yakın',
        'altyazı m k', 'izlediğiniz için teşekkürler', 'abone olmayı unutmayın',
        'bir sonraki videoda görüşürüz', 'bu ne kadar iyi bir şey', 'teşekkürler', 'sağ ol',
        'sağ olun', 'inşallah', 'bence', 'başlayın', 'yereyim', 'bazı', 'meseleler var',
        'o meşgul mu', 'kışın sütüyle alalandı', 'yüzme telsene', 'ıı', 'aa', 'öhm', 'şeyy',
        'neydi', 'bakalım ne diyecektim', 'şimdi şey', 'bir de', 'hani', 'şu', 'bu', 'o zaman',
        'altyazı', 'müzik', 'alkış', 'gülüşmeler', 'olay iyi', 'iyi seyirler', 'kanalıma abone olun',
        'beğenmeyi unutmayın',
    ],
}


def hepsi():
    """[(cumle, grup), ...]"""
    return [(c, grup) for grup, cumleler in NEGATIFLER.items() for c in cumleler]
