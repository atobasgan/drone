"""Gorev 4.1: her komut icin temel soyleyis sablonlari.

Bosluklar (parametreler.py doldurur):
  {metre}  goreli mesafe            -> "metre"
  {irtifa} mutlak irtifa            -> kalk'ta "irtifa_m", digerlerinde "metre"
  {derece} {saniye} {mps}           -> ayni adli alan
  {dakika} -> "saniye" (x60)        {kmsaat} -> "mps" (/3.6)
  {yon}    8 yonun yonelme hali     (kuzeye, sağa, ileri, geri ...)
  {dunya}  dunya yonu ad hali       (kuzey, güney, doğu, batı)
  {taraf}  8 yonun ad hali          (kuzey, sağ, ön, arka ...)  "X tarafına doğru"
  {sagsol} sağa / sola              {sagsol_ad} sağ / sol
  {yer}    yer turu yonelme hali    (hastaneye, eczaneye ...)
  {enlem} {boylam}

KURAL (etiketler elle yazilmis test setleriyle ayni):
  "X metre yüksel / yukarı çık"        -> yuksel (goreli)
  "X metreye çık", "irtifayı X'e getir"-> irtifaya_cik (mutlak, yerden)
  derecesi soylenmeyen donus           -> 90
  "havada kal", "olduğun yerde bekle"  -> dur (hemen dur, yerinde kal)
  "dur", "iptal", "acil", "stop" gecen cumle zaten LLM'e gitmez (hizli yolun acil
  kurali); bu yuzden dur DISINDAKI sablonlarda bu kelimeler yok.
"""

SABLONLAR = {
    'kalk': [
        'kalk', 'kalkış yap', 'havalan', 'kalkışa geç', 'uçuşa başla', 'havalanabilirsin',
        'motorları çalıştır ve kalk', 'yerden kalk', 'kalkış', 'kalkışı başlat', 'drone kalksın',
        '{irtifa} metreye kalk', '{irtifa} metre irtifaya kalk', '{irtifa} metreye havalan',
        '{irtifa} metre yüksekliğe kalk',
        '{irtifa} metreye kadar kalkış yap', 'kalkış yap irtifa {irtifa} metre',
        '{irtifa} metre yükseğe havalan',
    ],
    'in': [
        'in', 'iniş yap', 'yere in', 'inişe geç', 'yere kon', 'iniş',
        'inişi başlat', 'yere iniş yap', 'olduğun yere in', 'bulunduğun yere iniş yap',
        'aşağıya in ve yere kon', 'teker koy', 'iniş yapabilirsin', 'yere in artık',
    ],
    'yuksel': [
        '{metre} metre yüksel', '{metre} metre yukarı çık', '{metre} metre tırman',
        'yukarı {metre} metre', 'yukarı {metre} metre çık', 'irtifayı {metre} metre artır',
        '{metre} metre daha yüksel', '{metre} metre irtifa kazan', '{metre} metre yukarıya çık',
        'yüksekliği {metre} metre artır', '{metre} metre yukarı', 'bir {metre} metre yüksel',
        'irtifanı {metre} metre yükselt', '{metre} metre daha yukarı çık', '{metre} metre yukarı tırman',
        '{metre} metre irtifa al', 'yüksel {metre} metre',
    ],
    'alcal': [
        '{metre} metre alçal', '{metre} metre aşağı in', '{metre} metre in',
        'aşağı {metre} metre', 'aşağı {metre} metre in', 'irtifayı {metre} metre azalt',
        '{metre} metre daha alçal', '{metre} metre irtifa kaybet', '{metre} metre aşağıya in',
        'yüksekliği {metre} metre azalt', '{metre} metre aşağı', '{metre} metre düş',
        'irtifanı {metre} metre düşür', '{metre} metre daha aşağı in', '{metre} metre alçalt',
        'alçal {metre} metre',
    ],
    'irtifaya_cik': [
        '{irtifa} metreye çık', '{irtifa} metreye in', '{irtifa} metreye yüksel',
        '{irtifa} metreye alçal', 'irtifayı {irtifa} metreye getir', 'irtifayı {irtifa} metreye çıkar',
        'irtifayı {irtifa} metreye düşür', 'irtifayı {irtifa} metre yap', 'yüksekliği {irtifa} metre yap',
        'yüksekliği {irtifa} metreye ayarla', '{irtifa} metre irtifaya çık', '{irtifa} metre irtifaya in',
        '{irtifa} metre irtifaya yüksel', '{irtifa} metre yüksekliğe çık', 'irtifa {irtifa} metre olsun',
        '{irtifa} metre irtifada uç', 'yüksekliğini {irtifa} metreye getir', '{irtifa} metreye kadar çık',
        '{irtifa} metreye kadar alçal', 'irtifayı {irtifa} metreye indir', 'irtifanı {irtifa} metreye ayarla',
    ],
    'git_yon': [
        '{yon} {metre} metre git', '{metre} metre {yon} git', '{yon} {metre} metre uç',
        '{yon} {metre} metre ilerle', '{metre} metre {yon} ilerle', '{yon} doğru {metre} metre git',
        '{yon} {metre} metre', '{metre} metre {yon}', '{yon} {metre} metre hareket et',
        '{yon} {metre} metre kadar git', '{taraf} tarafına doğru {metre} metre git',
        '{taraf} tarafa {metre} metre git', '{metre} metre {yon} doğru uç',
        '{dunya} yönünde {metre} metre git', '{dunya} yönünde {metre} metre uç',
        '{dunya} yönüne {metre} metre ilerle', '{metre} metre {dunya} yönünde git',
        '{dunya} istikametinde {metre} metre git',
    ],
    'don': [
        '{sagsol} dön', '{sagsol} {derece} derece dön', '{derece} derece {sagsol} dön',
        '{sagsol} {derece} derece', '{sagsol} çevril', '{sagsol} {derece} derece çevril',
        '{sagsol_ad} tarafa dön', '{sagsol_ad} tarafa {derece} derece dön',
        'kendi etrafında {sagsol} {derece} derece dön', 'burnunu {sagsol} çevir',
        'burnunu {sagsol} {derece} derece çevir', '{sagsol} doğru {derece} derece dön',
        '{derece} derece {sagsol} çevril', '{sagsol} {derece} derecelik dönüş yap',
        '{sagsol} dönüş yap', 'yüzünü {sagsol} çevir', '{sagsol_ad} yöne {derece} derece dön',
    ],
    'git_koordinat': [
        'enlem {enlem} boylam {boylam} noktasına git', '{enlem} {boylam} koordinatına git',
        'koordinat {enlem} {boylam} git', 'enlem {enlem} boylam {boylam}',
        '{enlem} enlem {boylam} boylama uç', 'şu koordinata git enlem {enlem} boylam {boylam}',
        'enlem {enlem} boylam {boylam} konumuna uç',
        'enlem {enlem} boylam {boylam} noktasına {irtifa} metre irtifada git',
    ],
    'yakin_yere_git': [
        'en yakın {yer} git', 'bana en yakın {yer} uç', 'en yakın {yer} götür',
        'yakındaki {yer} git', 'en yakın {yer} doğru uç', 'buraya en yakın {yer} git',
        'en yakın {yer} kadar uç', 'hemen en yakın {yer} git',
    ],
    'bekle': [
        '{saniye} saniye bekle', '{saniye} saniye havada bekle', '{saniye} saniye olduğun yerde bekle',
        '{saniye} saniye boyunca bekle', 'bekle {saniye} saniye',
        '{saniye} saniye kadar bekle', '{saniye} saniye havada asılı kal', '{saniye} saniye beklemede kal',
        '{dakika} dakika bekle', '{dakika} dakika havada bekle', '{dakika} dakika boyunca bekle',
        '{saniye} saniye orada kal', '{saniye} saniye hover yap',
    ],
    'hiz_ayarla': [
        'hızı {mps} metre bölü saniye yap', 'hızını {mps} metre saniye yap', 'hızı {mps} m/s yap',
        'hızı {mps} metre saniyeye ayarla', 'hızını {mps} metre saniyeye düşür',
        'hızını {mps} metre saniyeye çıkar', 'hız {mps} metre saniye olsun', '{mps} metre saniye hızla uç',
        'saniyede {mps} metre hızla git', 'hızı {kmsaat} km/saat yap', 'hızını {kmsaat} kilometre saat yap',
        'saatte {kmsaat} kilometre hızla uç', 'hızını saniyede {mps} metreye ayarla',
    ],
    'eve_don': [
        'eve dön', 'eve git', 'üsse dön', 'kalkış noktasına dön', 'başlangıç noktasına dön',
        'eve geri dön', 'geldiğin yere geri dön', 'başladığın yere dön', 'kalktığın yere dön',
        'kalkış noktasına geri dön', 'eve dönüş yap', 'başlangıç noktasına geri git',
        'üsse geri dön', 'kalkış yaptığın yere dön', 'geri dön ve eve git',
    ],
    'dur': [
        'dur', 'hemen dur', 'olduğun yerde dur', 'havada kal', 'olduğun yerde kal', 'yerinde kal',
        'hareket etme', 'olduğun yerde bekle', 'havada asılı kal', 'hover yap', 'beklemede kal',
        'bekle', 'dur orada', 'kıpırdama', 'sabit kal',
    ],
}

# Cok adimli cumleler icin baglaclar: "A {baglac} B". "önce A sonra B" ayrica uretilir.
BAGLACLAR = ['sonra', 've', 'ardından', 'daha sonra', 'ondan sonra', 'arkasından', 'sonrasında']

# Cok adimda ilk fiil cogu zaman ulac olur: "yükselip", "dönüp", "bekleyip".
# Cumle = ULAC_ILK[komut1] + " " + SABLONLAR[komut2] icinden bir sablon.
ULAC_ILK = {
    'kalk': ['kalkıp', 'havalanıp', 'kalkış yapıp'],
    'yuksel': ['{metre} metre yükselip', '{metre} metre yukarı çıkıp', '{metre} metre tırmanıp'],
    'alcal': ['{metre} metre alçalıp', '{metre} metre aşağı inip'],
    'irtifaya_cik': ['{irtifa} metreye çıkıp', '{irtifa} metreye inip', 'irtifayı {irtifa} metreye getirip'],
    'git_yon': ['{yon} {metre} metre gidip', '{yon} {metre} metre ilerleyip', '{yon} {metre} metre uçup'],
    'don': ['{sagsol} dönüp', '{sagsol} {derece} derece dönüp'],
    'bekle': ['{saniye} saniye bekleyip'],
    'yakin_yere_git': ['en yakın {yer} gidip'],
}
