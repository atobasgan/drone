"""16 kHz mono WAV okuma / yazma (standart kutuphane + numpy).

Kayitlari dogrudan 16 kHz mono 16-bit al (kayit_al bunu yapar). Farkli
ornekleme hizindaki dosyalar dogrusal enterpolasyonla cevrilir; bu kaba bir
yontemdir, olcum setinde kullanma.
"""
import wave

import numpy as np

HZ = 16000


def yeniden_ornekle(x, kaynak_hz, hedef_hz=HZ):
    if kaynak_hz == hedef_hz or len(x) == 0:
        return x
    n = int(round(len(x) * hedef_hz / kaynak_hz))
    t = np.linspace(0, len(x) - 1, n)
    return np.interp(t, np.arange(len(x)), x).astype(np.float32)


def wav_oku(yol, hedef_hz=HZ):
    """WAV -> float32 [-1, 1], mono, hedef_hz."""
    with wave.open(str(yol), 'rb') as w:
        kanal, genislik, hz = w.getnchannels(), w.getsampwidth(), w.getframerate()
        ham = w.readframes(w.getnframes())
    if genislik != 2:
        raise ValueError(f'{yol}: yalnızca 16-bit PCM WAV destekleniyor')
    x = np.frombuffer(ham, dtype='<i2').astype(np.float32) / 32768.0
    if kanal > 1:
        x = x.reshape(-1, kanal).mean(axis=1)
    return yeniden_ornekle(x, hz, hedef_hz)


def wav_yaz(yol, x, hz=HZ):
    """float32 [-1, 1] ya da int16 dizisini 16-bit mono WAV olarak yazar."""
    x = np.asarray(x)
    if x.dtype != np.int16:
        x = (np.clip(x, -1.0, 1.0) * 32767).astype('<i2')
    with wave.open(str(yol), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(hz)
        w.writeframes(x.tobytes())
