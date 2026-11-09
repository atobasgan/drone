import re

import pytest

from voice_input.stt_sozlugu import (DRONE_SOZLUGU, ESKI_SOZLUK, PROMPT_SINIRI, siniri_kontrol_et,
                                     sozluk_sec, token_sayisi)


def whisper_tokenizer():
    """Whisper small'in tokenizer'i (indirilmis modelden); yoksa test atlanir."""
    tokenizers = pytest.importorskip('tokenizers')
    hub = pytest.importorskip('huggingface_hub')
    yol = hub.try_to_load_from_cache('Systran/faster-whisper-small', 'tokenizer.json')
    if not isinstance(yol, str):
        pytest.skip('faster-whisper-small indirilmemiş (scripts/ses_kur.sh)')
    return tokenizers.Tokenizer.from_file(yol)


def test_sozluk_whisper_sinirina_sigar():
    t = whisper_tokenizer()
    n = token_sayisi(t, DRONE_SOZLUGU)
    assert n <= PROMPT_SINIRI, f'{n} token: Whisper baştaki {n - PROMPT_SINIRI} tokeni atar'
    assert n >= 180, 'sınırın çoğu kullanılmalı'


def test_sinir_asilirsa_uyarir():
    t = whisper_tokenizer()
    with pytest.warns(UserWarning, match='atilacak'):
        siniri_kontrol_et(t, DRONE_SOZLUGU + ' ' + DRONE_SOZLUGU)


def test_sozluk_kurallari():
    # Ekler kesme isaretsiz yazilir ("sol'a", "irtifa'yı" degil); sayilar rakamla.
    assert "'" not in DRONE_SOZLUGU
    assert re.search(r'\d+ metre', DRONE_SOZLUGU)
    # Olcumde en sik bozulan kelimeler sozlukte olmali.
    kucuk = DRONE_SOZLUGU.replace('İ', 'i').lower()
    for kelime in ('metre', 'sağa', 'sola', 'ilerle', 'yüksel', 'alçal', 'sonra', 'ardından', 'acil dur',
                   'vazgeç', 'iniş yap', 'kuzeye', 'güneye', 'irtifa al', 'derece', 'saniye'):
        assert kelime in kucuk, kelime
    # Emir kipi, noktayla biten cumleler.
    assert DRONE_SOZLUGU.count('.') >= 25
    # Sozlugun sonu uydurmada kopyalanir: son cumle durdurma olmali, hareket degil.
    assert DRONE_SOZLUGU.endswith('Dur.')


def test_sozluk_sec(tmp_path):
    assert sozluk_sec('yeni') == DRONE_SOZLUGU
    assert sozluk_sec('eski') == ESKI_SOZLUK
    assert sozluk_sec('yok') == ''
    dosya = tmp_path / 's.txt'
    dosya.write_text('# yorum\nKalk.\nİn.\n', encoding='utf-8')
    assert sozluk_sec(str(dosya)) == 'Kalk. İn.'


def test_sozlukten_kopya():
    from voice_input.stt import sozlukten_kopya_mi
    sozluk = 'Yüksel. Tırman. İrtifa al. Önce 20 metre yüksel, sonra kuzeye 50 metre git.'
    assert sozlukten_kopya_mi('Önce 20 metre yüksel, sonra kuzeye', sozluk)
    assert sozlukten_kopya_mi('yüksel', sozluk)       # yalniz sessizse atilir (no_speech_prob)
    assert sozlukten_kopya_mi('İrtifa al, yüksel, irtifa al.', sozluk)   # sira karisik, tekrarli
    assert not sozlukten_kopya_mi('30 metre alçal', sozluk)
    assert not sozlukten_kopya_mi('yüksel', None)
    assert not sozlukten_kopya_mi('', sozluk)


def seg(metin, nsp=0.02, lp=-0.2, cr=1.0):
    from types import SimpleNamespace
    return SimpleNamespace(text=' ' + metin, no_speech_prob=nsp, avg_logprob=lp, compression_ratio=cr)


def test_segment_suzgeci():
    from voice_input.stt import segmentleri_suz
    sozluk = 'Kalkış yap. Yüksel. İrtifa kaybet. Acil dur. Dur.'
    # Normal konusma gecer
    assert segmentleri_suz([seg('20 metre yüksel.')], sozluk)[0] == '20 metre yüksel.'
    # Yalniz gurultude sozlukten kopya (olcumdeki gercek degerler): atilir
    metin, atilan = segmentleri_suz([seg('Yüksel, irtifa kaybet.', nsp=0.88, lp=-0.86)], sozluk)
    assert metin == '' and 'kopya' in atilan[0]
    # Kopya da olsa durdurma atilmaz
    assert segmentleri_suz([seg('Dur.', nsp=0.7, lp=-0.7)], sozluk)[0] == 'Dur.'
    # Tekrar dongusu atilir; durdurma dongusunden bir kez "Dur." kalir
    assert segmentleri_suz([seg('5 metre, ' * 30, cr=12.0)], sozluk)[0] == ''
    assert segmentleri_suz([seg('Dur. ' * 20, cr=29.4)], sozluk)[0] == 'Dur.'
    # Eski kural: sessiz + dusuk olasilik
    assert segmentleri_suz([seg('hmm', nsp=0.9, lp=-1.5)], sozluk)[0] == ''
    # Sozluk yokken kopya kurali calismaz
    assert segmentleri_suz([seg('Yüksel.', nsp=0.88, lp=-0.8)], None)[0] == 'Yüksel.'
