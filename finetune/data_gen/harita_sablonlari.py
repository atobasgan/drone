"""Gorev 5.4: "Anıtkabir'e git" -> yere_git {ad} icin sablonlar ve yer adlari.

Etiket kurali (tek ve basit): ad = cumlede gecen yer adinin YALIN hali, normalize edilmis
(kucuk harf). "kızılay meydanı'na uç" -> {"komut":"yere_git","ad":"kızılay meydanı"}.
Model adi cumleden KOPYALAR; harita servisi (Nominatim / Google) buyuk-kucuk harfe bakmaz.

Yer adlari train / val / test'e AYRILIR: testteki yerler egitimde hic gorulmez,
model ezber degil "kopyalama" kuralini ogrenmeli. Sablonlar da ayni sekilde ayrilir.
Yer adlarinda sayi ve acil kelime (dur, iptal, acil, stop) YOK: kontrol.py kurallari.
"""

# Bosluklar: {yer_e} yonelme hali ("anıtkabir'e"), {yer} yalin hal ("anıtkabir")
YERE_GIT_SABLONLARI = [
    '{yer_e} git', '{yer_e} uç', '{yer_e} doğru uç', '{yer_e} doğru git', '{yer_e} kadar uç',
    '{yer_e} götür', 'hemen {yer_e} git', 'şimdi {yer_e} uç', '{yer_e} gidelim', '{yer_e} uçar mısın',
    '{yer_e} gider misin', '{yer_e} git lütfen', 'lütfen {yer_e} uç', '{yer} üzerine uç',
    '{yer} üstüne git', '{yer} tarafına uç', '{yer} yakınına git', '{yer_e} yönel', 'rotayı {yer_e} çevir',
    '{yer_e} gitmeni istiyorum', '{yer_e} bir uç', 'drone {yer_e} gitsin', '{yer} konumuna git',
    '{yer_e} uçuş yap', '{yer_e} kadar git', 'bizi {yer_e} götür', '{yer} üzerine git', '{yer_e} rota çiz',
    '{yer} civarına uç', 'haydi {yer_e} uç',
]

# Cok adimli cumlede yere_git ilk adimsa ulac: "anıtkabir'e gidip in"
YERE_GIT_ULAC = ['{yer_e} gidip', '{yer_e} uçup', '{yer_e} varınca', '{yer} üzerine gidip']

# (yalin ad, iyelik eki var mi). Iyelikli birlesik adlar "-na/-ne" alir: "Gençlik Parkı'na".
YER_ADLARI = [
    # Ankara
    'Anıtkabir', 'Kızılay Meydanı', 'Atakule', 'Gençlik Parkı', 'Ankara Kalesi', 'Kocatepe Camii',
    'Ulus Meydanı', 'Hamamönü', 'Seğmenler Parkı', 'Botanik Parkı', 'Dikmen Vadisi', 'Eymir Gölü',
    'Mogan Gölü', 'Ankara Garı', 'Tunalı Hilmi Caddesi', 'Armada', 'Kuğulu Park', 'Aşti',
    'Esenboğa Havalimanı', 'Atatürk Orman Çiftliği', 'ODTÜ', 'Bilkent', 'Hacettepe Hastanesi',
    'Gazi Hastanesi', 'Çankaya Köşkü', 'Etimesgut', 'Gölbaşı', 'Kurtuluş Parkı', 'Abdi İpekçi Parkı',
    'Harikalar Diyarı', 'Ankapark', 'Sıhhiye Köprüsü', 'Ankara Üniversitesi', 'Kavaklıdere', 'Çayyolu',
    'Batıkent', 'Keçiören', 'Altınpark', 'Hacı Bayram Camii', 'Cebeci Stadyumu', 'Kuğulu Göl',
    'Beypazarı', 'Ahlatlıbel', 'Göksu Parkı', 'Sakarya Caddesi', 'Ulus Heykeli', 'Tandoğan',
    # Istanbul, Izmir ve digerleri
    'Galata Kulesi', 'Kız Kulesi', 'Taksim Meydanı', 'Sultanahmet Camii', 'Ayasofya', 'Dolmabahçe Sarayı',
    'Emirgan Korusu', 'Maçka Parkı', 'Kadıköy İskelesi', 'Belgrad Ormanı', 'Saat Kulesi', 'Kordon',
    'Kültürpark', 'Konak Meydanı', 'Alsancak', 'Bostanlı', 'Karşıyaka Çarşısı', 'Kemeraltı',
    # adi konmus genel yerler
    'Merkez Camii', 'Belediye Binası', 'Hükümet Konağı', 'Şehir Stadyumu', 'Otogar', 'Kampüs',
    'Futbol Sahası', 'Spor Salonu', 'Köy Meydanı', 'Liman', 'Deniz Feneri', 'Su Deposu', 'Baraj Gölü',
    'Kuzguncuk', 'Çamlıca Tepesi', 'Orman Evi', 'Fabrika', 'Tren İstasyonu', 'Şehir Hastanesi',
]

# "bir yere git" turu: yer belirsiz -> bilinmiyor. Faz 4'teki "en yakın yere uç" negatiflerine ek.
HARITA_NEGATIFLERI = [
    'oraya git', 'şuraya uç', 'bir yere git', 'herhangi bir yere uç', 'başka bir yere git',
    'oraya doğru uç', 'şu tarafa git', 'bilmediğin bir yere git', 'güzel bir yere uç', 'uzak bir yere git',
    'bir yerlere uç', 'şuraya kadar git', 'beni bir yere götür', 'gideceğin yere git', 'o yere uç',
    'bir yere uçalım', 'oraya kadar uç', 'şu binaya git', 'şuradaki yere uç', 'herhangi bir yere götür',
    'gitmek istediğim yere git', 'oraya bir uç', 'bir yere doğru git', 'nereye gidiyorsun',
    'anıtkabir nerede', 'kızılay ne kadar uzak', 'galata kulesi kaç metre', 'atakule güzel mi',
    'gençlik parkını sever misin', 'ankara kalesi tarihi bir yer',
]

_KALIN = set('aıou')
_INCE = set('eiöü')


def _son_unlu(kelime):
    for h in reversed(kelime):
        if h in _KALIN or h in _INCE:
            return h
    return 'e'


def yonelme(ad):
    """Yalin yer adi -> yonelme hali, kesme isaretiyle: anıtkabir -> anıtkabir'e,
    gençlik parkı -> gençlik parkı'na, odtü -> odtü'ye. Ad normalize edilmis (kucuk harf) gelir."""
    ek = 'a' if _son_unlu(ad) in _KALIN else 'e'
    son = ad[-1]
    if son in _KALIN or son in _INCE:
        # birlesik ad + iyelik (parkı, camii, meydanı) -> n; tek kelime unluyle biten -> y
        tampon = 'n' if ' ' in ad and son in 'ıiuü' else 'y'
        return f"{ad}'{tampon}{ek}"
    return f"{ad}'{ek}"
