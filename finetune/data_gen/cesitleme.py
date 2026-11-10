"""Gorev 4.2: dogal soyleyisler (paraphrase).

sablonlar.py'deki temel kaliplarin gercek konusmadaki halleri:
  gunluk  : "ya şey bi elli metre yükselsene", "kırk metre kadar yükselir misin"
  devrik  : "yüksel elli metre", "git kuzeye yüz metre"
  kibar   : "lütfen ...", "... yapar mısın", "rica etsem ..."
  dolgu   : "hadi", "tamam şimdi", "eee", "şimdi de"
Bosluklar ve etiket kurallari sablonlar.py ile aynidir; etiketi yine kod kurar.
Bu cumleler bir LLM yardimiyla yazildi ve elle gozden gecirildi (MIMARI 7, yontem 2).
Daha fazlasi icin: llm_cesitle.py (bir LLM sunucusundan yeni cumle ister, dogrular).
"""

CESITLEME = {
    'kalk': [
        'hadi kalk', 'tamam kalkabilirsin', 'kalk bakalım', 'şimdi kalkış yap', 'lütfen havalan',
        'kalkar mısın', 'havalan hadi', 'haydi kalkışa geçelim', 'kalkış yapar mısın lütfen',
        'tamam şimdi havalan', 'ee kalk artık', 'kalk ve {irtifa} metreye çık',
        'bir {irtifa} metreye kadar kalksana', '{irtifa} metreye kalkar mısın',
        'lütfen {irtifa} metre irtifaya havalan', 'havalan {irtifa} metreye',
    ],
    'in': [
        'hadi in', 'artık in', 'yere insene', 'lütfen iniş yap', 'iner misin', 'tamam in bakalım',
        'aşağı in ve yere kon', 'yere kon artık', 'şimdi iniş yapalım', 'inebilirsin',
        'iniş yapar mısın', 'hadi yere in', 'yavaşça yere in', 'güvenli bir şekilde in',
    ],
    'yuksel': [
        'ya şey bi {metre} metre yükselsene', 'biraz yükselsene {metre} metre kadar',
        '{metre} metre kadar yükselir misin', 'lütfen {metre} metre yüksel', 'hadi {metre} metre yüksel',
        'yüksel {metre} metre', 'bir {metre} metre daha yüksel bakalım', '{metre} metre yukarı çıksana',
        'şimdi {metre} metre yukarı çık', 'tamam {metre} metre tırman', 'yukarı çık {metre} metre',
        '{metre} metre yükselir misin lütfen', 'eee {metre} metre yüksel', 'rica etsem {metre} metre yüksel',
        '{metre} metre kadar yukarı çık', 'biraz daha yüksel {metre} metre',
    ],
    'alcal': [
        'ya şey bi {metre} metre alçalsana', 'biraz alçal {metre} metre kadar',
        '{metre} metre kadar alçalır mısın', 'lütfen {metre} metre alçal', 'hadi {metre} metre aşağı in',
        'alçal {metre} metre', '{metre} metre aşağı insene', 'şimdi {metre} metre alçal',
        'tamam {metre} metre aşağı in', 'aşağı in {metre} metre', '{metre} metre alçalır mısın lütfen',
        'bir {metre} metre daha alçal', '{metre} metre kadar aşağı in', 'biraz daha alçal {metre} metre',
    ],
    'irtifaya_cik': [
        '{irtifa} metreye çıkar mısın', 'lütfen {irtifa} metreye çık', 'çık {irtifa} metreye',
        'irtifayı {irtifa} metreye getirir misin', 'hadi {irtifa} metreye in',
        'yüksekliği {irtifa} metreye ayarlar mısın', 'tamam {irtifa} metre irtifaya çık',
        'şimdi {irtifa} metreye alçal', 'in {irtifa} metreye', '{irtifa} metre irtifaya inebilirsin',
        'irtifa {irtifa} metre olacak şekilde ayarla', '{irtifa} metre yüksekliğe çıksana',
    ],
    'git_yon': [
        'ya şey bi {yon} {metre} metre gitsene', '{yon} {metre} metre kadar gider misin',
        'biraz {yon} doğru git {metre} metre kadar', 'lütfen {yon} {metre} metre git',
        'git {yon} {metre} metre',
        'hadi {yon} {metre} metre uç', '{yon} doğru {metre} metre ilerler misin', 'uç {yon} {metre} metre',
        '{metre} metre {yon} gitsene', 'tamam şimdi {yon} {metre} metre git',
        '{taraf} tarafa doğru {metre} metre gel',
        '{taraf} tarafına {metre} metre kadar uç', 'şimdi de {yon} {metre} metre git',
        '{dunya} yönünde {metre} metre kadar ilerle', 'rica etsem {yon} {metre} metre git',
        'ilerle {yon} {metre} metre',
    ],
    'don': [
        '{sagsol} döner misin', 'hadi {sagsol} dön', 'lütfen {sagsol} {derece} derece dön',
        'dön {sagsol} {derece} derece', '{sagsol} bir {derece} derece dönsene', 'biraz {sagsol} dön',
        'tamam şimdi {sagsol} dön', '{sagsol_ad} tarafa doğru {derece} derece çevril',
        'burnunu {sagsol} çevirir misin', '{sagsol} doğru dön', 'kendi etrafında {sagsol} dön',
        '{derece} derece {sagsol} döner misin', 'şimdi de {sagsol} dön',
    ],
    'git_koordinat': [
        'lütfen enlem {enlem} boylam {boylam} noktasına git', 'şu konuma uç enlem {enlem} boylam {boylam}',
        'enlem {enlem} boylam {boylam} noktasına gider misin', 'koordinatlar {enlem} {boylam} oraya git',
    ],
    'yakin_yere_git': [
        'en yakın {yer} gider misin', 'lütfen en yakın {yer} git',
        'hadi en yakın {yer} uç', 'şuradaki en yakın {yer} git', 'en yakın {yer} gidelim',
        'yakınlardaki {yer} uç',
    ],
    'bekle': [
        'bir {saniye} saniye bekle', 'şurada {saniye} saniye bekle', 'lütfen {saniye} saniye bekle',
        '{saniye} saniye bekler misin', 'hadi {saniye} saniye bekle', 'bekle bakalım {saniye} saniye',
        '{saniye} saniye havada kal', '{dakika} dakika bekler misin', 'bir {dakika} dakika havada kal',
        '{saniye} saniye kadar orada bekle',
    ],
    'hiz_ayarla': [
        'hızını {mps} metre saniyeye ayarlar mısın', 'lütfen hızı {mps} metre saniye yap',
        'hız {mps} metre saniye', '{mps} metre saniyeyle uç', 'hızını biraz düşür {mps} metre saniye yap',
        'hızlan {mps} metre saniyeye', 'yavaşla {mps} metre saniyeye', 'saatte {kmsaat} kilometreyle git',
        'hızını {kmsaat} km/saat yapar mısın',
    ],
    'eve_don': [
        'hadi eve dön', 'tamam eve dönebilirsin', 'lütfen eve dön', 'eve döner misin', 'artık eve dön',
        'üsse geri gel', 'geldiğin yere dön', 'başladığımız yere geri dön', 'kalkış yerine geri gel',
        'şimdi eve dönelim', 'görev bitti eve dön', 'evine dön', 'eve geri gel',
    ],
    'dur': [
        'dur dur', 'lütfen dur', 'hemen orada dur', 'olduğun yerde kal lütfen', 'havada bekle',
        'tamam dur', 'dur bekle', 'hareket etme orada kal', 'bir saniye dur', 'stop', 'acil dur',
        'iptal', 'vazgeç', 'yeter dur',
    ],
}

# Konusmada komutun basina/sonuna eklenen dolgu sozleri (anlam degismez).
DOLGU_BAS = ['tamam', 'şimdi', 'hadi', 'drone', 'tamam şimdi', 'şey', 'evet', 'peki', 'ee', 'bak',
             'hemen', 'haydi', 'şimdi de', 'tamam o zaman', 'pekala']
DOLGU_SON = ['lütfen', 'hemen', 'hadi', 'bakalım', 'artık', 'şimdi', 'tamam mı']


def dolgu_ekle(rng, cumle):
    """'eve dön' -> 'tamam şimdi eve dön' ya da 'eve dön lütfen'."""
    if rng.random() < 0.6:
        return f'{rng.choice(DOLGU_BAS)} {cumle}'
    return f'{cumle} {rng.choice(DOLGU_SON)}'
