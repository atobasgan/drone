"""Gecikme CSV'si ve ozet tablosu (Gorev 3.5, MIMARI 9.3). ROS'tan bagimsizdir.

Damgalar (nanosaniye, yoksa 0):
  t0 konusma bitti (VAD)   t1 STT bitti        tm parser metni aldi
  t2 komut JSON hazir      t3 yurutucu aldi    t4 ilk yeni setpoint
  t5 telemetride hiz degisti
Not: t0, VAD'in bitis sessizligini bekledikten SONRAki andir; konusmanin
gercekten bittigi an t0 - bitis_sessizlik_ms'dir (dosya modunda bu bekleme yok).
"""
import csv
import statistics

DAMGALAR = ('t0', 't1', 'tm', 't2', 't3', 't4', 't5')
CSV_ALANLARI = ('zaman', 'metin', 'kaynak', 'ses_kaynagi', 'sonuc') + DAMGALAR

# (ad, baslangic, bitis, aciklama)
ASAMALAR = (
    ('stt', 't0', 't1', 'STT (konuşma bitti → metin)'),
    ('stt_parser', 't1', 'tm', 'stt_node → parser (ROS)'),
    ('parser', 'tm', 't2', 'parser (normalize + hızlı yol / LLM)'),
    ('parser_yurutucu', 't2', 't3', 'parser → yürütücü (ROS)'),
    ('setpoint', 't3', 't4', 'yürütücü → ilk setpoint'),
    ('px4', 't4', 't5', 'PX4 tepkisi (setpoint → hız değişimi)'),
    ('toplam', 't0', 't5', 'TOPLAM (konuşma bitti → drone tepki verdi)'),
    ('toplam_komut', 't0', 't2', 'konuşma bitti → komut hazır'),
)


def yuzdelik(degerler, p):
    s = sorted(degerler)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    alt = int(k)
    ust = min(alt + 1, len(s) - 1)
    return s[alt] + (s[ust] - s[alt]) * (k - alt)


def csv_oku(yol):
    with open(yol, encoding='utf-8', newline='') as f:
        satirlar = list(csv.DictReader(f))
    for s in satirlar:
        for d in DAMGALAR:
            s[d] = int(s[d] or 0)
    return satirlar


def asama_sureleri(satirlar, bas, son):
    return [(s[son] - s[bas]) / 1e6 for s in satirlar if s[bas] and s[son] and s[son] >= s[bas]]


def ozet(satirlar):
    """{asama: {n, ort, p50, p95, aciklama}} — yalnizca iki damgasi da olan satirlar."""
    sonuc = {}
    for ad, bas, son, aciklama in ASAMALAR:
        ms = asama_sureleri(satirlar, bas, son)
        sonuc[ad] = {
            'aciklama': aciklama, 'n': len(ms),
            'ort': statistics.mean(ms) if ms else 0.0,
            'p50': yuzdelik(ms, 50), 'p95': yuzdelik(ms, 95),
        }
    return sonuc


def en_yavas(oz):
    """TOPLAM satirlari haric ortalamasi en buyuk asama."""
    adaylar = [(v['ort'], ad) for ad, v in oz.items() if not ad.startswith('toplam') and v['n']]
    return max(adaylar)[1] if adaylar else None


def tablo_md(oz, baslik=''):
    satirlar = [f'\n{baslik}\n' if baslik else '',
                '| aşama | n | ort ms | p50 ms | p95 ms |\n|---|---|---|---|---|\n']
    for ad, v in oz.items():
        satirlar.append(f'| {v["aciklama"]} | {v["n"]} | {v["ort"]:.1f} | {v["p50"]:.1f} '
                        f'| {v["p95"]:.1f} |\n')
    return ''.join(satirlar)


def kaynaga_gore(satirlar):
    """Komut kaynagina (hizli_yol, llm, acil...) gore toplam sureler."""
    gruplar = {}
    for s in satirlar:
        gruplar.setdefault(s['kaynak'] or '?', []).append(s)
    return {k: ozet(v) for k, v in sorted(gruplar.items())}
