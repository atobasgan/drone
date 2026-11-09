"""Whisper initial_prompt icin drone sozlugu (DRONE_SOZLUGU.txt: tasarim ve olcumler).

Whisper bir LLM degildir; "dikkatli cevir" gibi talimatlari anlamaz. initial_prompt,
cozucuye (decoder) "bu kaydin ONCESINDE soylenmis metin" olarak verilir; model hem
kelimelerine hem de USLUBUNE (emir kipi, rakamla sayi, noktalama) yatkinlasir.

Uc kural (olcumlerden):
  1. Emir kipi, kisa, noktayla biten cumleler. Whisper Turkcede emirleri anlatiya
     cevirir ("yüksel" -> "yükseldi", "git" -> "gittik"); ornek emirler bunu duzeltir.
  2. Sayilar rakamla, ekler kesme isaretsiz ("50 metreye"); "metre" bol gecer
     (yoksa "meter" yazar).
  3. 223 token sinirina sigmali. faster-whisper fazlasinin BASINI keser; Turkcede
     1 token ~2.4 karakter (ı, ş, ğ, ç pahali), yani sinir ~540 karakter, 850 degil.
     En etkili kisim sondadir (cozulen metne en yakin), zor kelimeler sona.
"""
import warnings

# faster-whisper: previous_tokens[-(max_length // 2 - 1):]  ->  448 // 2 - 1
PROMPT_SINIRI = 223

# Siralama bilerek boyle: en ETKILI ve uydurmada en cok kopyalanan kisim SON kisimdir.
# Sona guvenlik komutlari kondu: ses yokken Whisper sozlugun sonunu "duyarsa" drone kalkmaz,
# durur (olcumde sonu "Kalk." olan surum gurultuden 11/12 kez "Kalk." uydurdu).
DRONE_SOZLUGU = (
    # 1. kalkis / irtifa / inis. Tek heceli "Kalk." ve "İn." ayri cumle: yoksa "Kal.", "Kon.", "Bin."
    'Kalkış yap. Kalk. Havalan. Yüksel. Tırman. Yukarı çık. İrtifa al. 50 metreye çık. '
    'Alçal. Aşağı in. İrtifa kaybet. İniş yap. Yere in. İn. '
    # 2. yonlu ucus (yonelme eki: "sağa", "kuzeye"; Whisper "sağ", "kuzey" yazmasin)
    'İleri git. Geri git. Sağa git. Sola git. Kuzeye git. Güneye git. Doğuya git. Batıya git. '
    # 3. donus, hiz, bekleme
    'Sağa dön. Sola dön. Saat yönünde 90 derece dön. '
    'Hızı 5 metre bölü saniye yap. 10 saniye bekle. Havada kal. '
    # 4. cok adimli: once / sonra / ve / ardindan (kuyruk baglaclari kaybolmasin)
    'Önce 20 metre yüksel, sonra kuzeye 50 metre git. '
    'Sağa dön ve 100 metre ileri git. 30 metre alçal, ardından in. '
    '200 metre ilerle. 150 metre sonra ikinci sola gir. '
    # 5. guvenlik (sonda: en guclu etki + guvenli uydurma)
    'Fren yap. Motorları durdur. İptal. Vazgeç. Üsse dön. Eve dön. Acil dur. Dur.'
)

# Faz 3'teki ilk surum (olcumlerde karsilastirma icin).
ESKI_SOZLUK = (
    'Drone komutları: kalk, kalkış yap, in, iniş yap, yüksel, alçal, metre, '
    'metreye çık, irtifa, ileri, geri, sağa, sola, kuzeye, güneye, doğuya, batıya, '
    'git, dön, derece, bekle, saniye, hız, eve dön, dur, acil, en yakın hastane, '
    'eczane, benzinlik.'
)

SOZLUKLER = {'yeni': DRONE_SOZLUGU, 'eski': ESKI_SOZLUK, 'yok': ''}


def sozluk_sec(ad_ya_da_dosya):
    """'yeni' | 'eski' | 'yok' ya da bir .txt dosyasi (icindeki metin, satirlar birlestirilir)."""
    if ad_ya_da_dosya in SOZLUKLER:
        return SOZLUKLER[ad_ya_da_dosya]
    with open(ad_ya_da_dosya, encoding='utf-8') as f:
        return ' '.join(s.strip() for s in f if s.strip() and not s.startswith('#'))


def token_sayisi(hf_tokenizer, metin):
    """faster-whisper'in initial_prompt'u kodladigi gibi: ' ' + metin, ozel token yok."""
    return len(hf_tokenizer.encode(' ' + metin.strip(), add_special_tokens=False).ids)


def siniri_kontrol_et(hf_tokenizer, metin):
    """Sinir asilirsa uyar: Whisper metnin BASINI sessizce atar. Token sayisini dondurur."""
    n = token_sayisi(hf_tokenizer, metin) if metin else 0
    if n > PROMPT_SINIRI:
        warnings.warn(f'initial_prompt {n} token; Whisper yalnizca son {PROMPT_SINIRI} tokeni '
                      f'kullanir, bastaki {n - PROMPT_SINIRI} token atilacak', stacklevel=2)
    return n
