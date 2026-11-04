import numpy as np

from voice_input.etiketler import etiket_ekle, etiketleri_oku, karsilastir
from voice_input.stt import aday_ayristir, halusinasyon_mu, kelime_farklari
from voice_input.wav import wav_oku, wav_yaz, yeniden_ornekle


def test_aday_ayristir():
    assert aday_ayristir('small') == ('small', 'int8', 'auto')
    assert aday_ayristir('small:int8') == ('small', 'int8', 'auto')
    assert aday_ayristir('large-v3-turbo:float16@cuda') == ('large-v3-turbo', 'float16', 'cuda')
    assert aday_ayristir('kisi/whisper-tr-ct2:int8_float16@cuda') == \
        ('kisi/whisper-tr-ct2', 'int8_float16', 'cuda')


def test_halusinasyon():
    assert halusinasyon_mu('Altyazı M.K.')
    assert not halusinasyon_mu('10 m yüksel')


def test_kelime_farklari():
    assert kelime_farklari('10 m yüksel', '10 m yüksel') == []
    assert kelime_farklari('10 m alçal', '10 m açal') == [('alçal', 'açal')]
    assert kelime_farklari('sağa dön', 'sağa') == [('dön', '')]


def test_wav_gidis_donus(tmp_path):
    x = (np.sin(np.linspace(0, 100, 16000)) * 0.5).astype(np.float32)
    yol = tmp_path / 'a.wav'
    wav_yaz(yol, x)
    y = wav_oku(yol)
    assert len(y) == 16000 and np.abs(x - y).max() < 1e-3
    assert len(yeniden_ornekle(x, 16000, 8000)) == 8000


def test_etiketler_ve_karsilastir(tmp_path):
    csv_yolu = tmp_path / 'etiketler.csv'
    etiket_ekle(csv_yolu, 'a_001.wav', 'a', '10 metre yüksel', [{'komut': 'yuksel', 'metre': 10}])
    etiket_ekle(csv_yolu, 'a_002.wav', 'a', 'saat kaç', [{'komut': 'bilinmiyor'}])
    s = etiketleri_oku(csv_yolu)
    assert s[0]['yol'] == str(tmp_path / 'a_001.wav')
    assert karsilastir([{'komut': 'yuksel', 'metre': 10.0}], s[0]['beklenen']) == (True, True, False)
    assert karsilastir([{'komut': 'yuksel', 'metre': 100.0}], s[0]['beklenen']) == (False, True, False)
    assert karsilastir([], s[1]['beklenen']) == (True, True, True)
    assert karsilastir([{'komut': 'bekle', 'saniye': 60.0}], s[1]['beklenen']) == (False, False, True)
