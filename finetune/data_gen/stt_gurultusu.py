"""Gorev 4.3: STT hata taklidi. Model gercekte temiz metin degil Whisper ciktisi gorur.

Hatalar uydurma degil; Faz 3 olcumunde (DRONE_SOZLUGU.txt Bolum 5) Whisper'in
gercekten yaptiklari. Etiket DEGISMEZ: "sağ dön" hala {"komut":"don","yon":"sag"}.

Bilerek EKLENMEYENLER (anlami degistirir ya da tehlikeli):
  "kalk" -> "kal"   : "havada kal" ile karisir; model "kal"i kalkis sanmamali
  "in"   -> "bin"   : "bin" bir sayi (1000)
"""

# (dogru, yanlis duyulan): yalnizca butun kelime eslesirse uygulanir
KELIME_HATALARI = [
    ('metre', 'meter'), ('metre', 'metve'), ('metre', 'mete'),
    ('metreye', 'meteye'), ('metreye', 'metreyi'),
    ('sağa', 'sağ'), ('sola', 'sol'), ('sola', 'solu'),
    ('ilerle', 'ilerli'), ('ilerle', 'ileride'),
    ('alçal', 'alçalı'), ('alçal', 'alçak'),
    ('yüksel', 'yüksek'), ('yüksel', 'yükseldi'), ('yüksel', 'yükselt'),
    ('git', 'gitti'), ('git', 'gittik'),
    ('kuzeye', 'kuzey'), ('güneye', 'güney'), ('güneye', 'güneyi'),
    ('doğuya', 'doğu'), ('batıya', 'batı'),
    ('irtifayı', 'irtifa'), ('hızını', 'hızı'), ('hızı', 'hızlı'),
    ('ardından', 'ardında'), ('vazgeç', 'bazı geç'), ('dön', 'dönü'),
    ('derece', 'derecede'), ('saniye', 'saniyede'),
]

# Turkce harf kaybi (dusuk kaliteli STT / klavye)
ASCII = str.maketrans('ıışğçöüİŞĞÇÖÜ', 'iisgcouISGCOU')


def kelime_hatasi(rng, cumle):
    """Cumlede gecen kelimelerden birini, bilinen bir yanlis duyumla degistirir."""
    kelimeler = cumle.split()
    adaylar = [(i, yanlis) for i, k in enumerate(kelimeler)
               for dogru, yanlis in KELIME_HATALARI if k == dogru]
    if not adaylar:
        return cumle
    i, yanlis = rng.choice(adaylar)
    kelimeler[i] = yanlis
    return ' '.join(kelimeler)


def baglac_dusur(rng, cumle):
    """Kisa, vurgusuz baglaclar STT'de kaybolur: "kalk ve yüksel" -> "kalk yüksel"."""
    kelimeler = cumle.split()
    adaylar = [i for i, k in enumerate(kelimeler) if k == 've' and 0 < i < len(kelimeler) - 1]
    if not adaylar:
        return cumle
    del kelimeler[rng.choice(adaylar)]
    return ' '.join(kelimeler)


def whisper_bicimi(rng, cumle):
    """Whisper cumle basini buyuk yazar, sonuna nokta koyar, virgul ekler."""
    if not cumle:
        return cumle
    cumle = cumle[0].upper() + cumle[1:]
    if rng.random() < 0.3:
        cumle = cumle.replace(' sonra ', ', sonra ').replace(' ardından ', ', ardından ')
    return cumle + rng.choice(['.', '.', '!', ''])


def gurultu_ekle(rng, cumle):
    """Bir ya da birkac bozulma uygular. Hangi bozulmalarin uygulandigini da dondurur."""
    uygulanan = []
    if rng.random() < 0.6:
        yeni = kelime_hatasi(rng, cumle)
        if yeni != cumle:
            cumle, uygulanan = yeni, uygulanan + ['kelime']
    if rng.random() < 0.3:
        yeni = baglac_dusur(rng, cumle)
        if yeni != cumle:
            cumle, uygulanan = yeni, uygulanan + ['baglac']
    if rng.random() < 0.15:
        cumle, uygulanan = cumle.translate(ASCII), uygulanan + ['ascii']
    if rng.random() < 0.5:
        cumle, uygulanan = whisper_bicimi(rng, cumle), uygulanan + ['bicim']
    return cumle, uygulanan
