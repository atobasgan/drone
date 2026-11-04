"""recordings/etiketler.csv ve sonuc karsilastirma (Gorev 3.1 - 3.4).

etiketler.csv sutunlari: dosya, konusmaci, metin, beklenen
  dosya    : CSV'nin bulundugu klasore gore WAV adi (atakan_007.wav)
  metin    : okunan cumle
  beklenen : beklenen komut JSON'u ({"adimlar": [...]}, command_parser/schema.py)
"""
import csv
import json
import os

from command_parser.schema import bilinmiyor_mu, kanonik

ALANLAR = ['dosya', 'konusmaci', 'metin', 'beklenen']


def varsayilan_klasor():
    return os.path.join(os.environ.get('LLM_DRONE_DIR', '.'), 'recordings')


def etiketleri_oku(csv_yolu):
    """Her satir: dosya, konusmaci, metin, beklenen (adim listesi), yol (mutlak WAV yolu)."""
    klasor = os.path.dirname(os.path.abspath(csv_yolu))
    with open(csv_yolu, encoding='utf-8', newline='') as f:
        satirlar = list(csv.DictReader(f))
    for s in satirlar:
        s['beklenen'] = json.loads(s['beklenen'])['adimlar']
        s['yol'] = os.path.join(klasor, s['dosya'])
    return satirlar


def etiket_ekle(csv_yolu, dosya, konusmaci, metin, beklenen):
    yeni = not os.path.exists(csv_yolu)
    with open(csv_yolu, 'a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=ALANLAR)
        if yeni:
            w.writeheader()
        w.writerow({'dosya': dosya, 'konusmaci': konusmaci, 'metin': metin,
                    'beklenen': json.dumps({'adimlar': beklenen}, ensure_ascii=False)})


def cumleleri_oku(yol):
    """cumleler.jsonl: {"metin": ..., "beklenen": {"adimlar": [...]}}; # ile baslayan satir yorum."""
    with open(yol, encoding='utf-8') as f:
        return [json.loads(s) for s in f if s.strip() and not s.startswith('#')]


def yuzdelik(degerler, p):
    s = sorted(degerler)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    alt = int(k)
    ust = min(alt + 1, len(s) - 1)
    return s[alt] + (s[ust] - s[alt]) * (k - alt)


def karsilastir(uretilen, beklenen):
    """(tam_dogru, komut_dogru, negatif_mi). Bos uretilen = komut yok."""
    if bilinmiyor_mu(beklenen):
        return not uretilen, not uretilen, True
    tam = kanonik(uretilen) == kanonik(beklenen)
    komut = [a['komut'] for a in uretilen] == [a['komut'] for a in beklenen]
    return tam, komut, False
