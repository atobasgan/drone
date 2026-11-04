import csv

from latency_monitor.olcum import CSV_ALANLARI, csv_oku, en_yavas, kaynaga_gore, ozet, tablo_md
from latency_monitor.ozet import main

MS = 1_000_000


def satir(kaynak='hizli_yol', stt=500, parser=2, llm=0, t5=True):
    t0 = 1_000_000 * MS
    t1 = t0 + stt * MS
    tm = t1 + 1 * MS
    t2 = tm + (parser + llm) * MS
    t3 = t2 + 1 * MS
    t4 = t3 + 30 * MS
    return {'zaman': '', 'metin': 'x', 'kaynak': kaynak, 'ses_kaynagi': 'dosya', 'sonuc': 'kabul',
            't0': t0, 't1': t1, 'tm': tm, 't2': t2, 't3': t3, 't4': t4,
            't5': t4 + 60 * MS if t5 else 0}


def test_ozet_ve_en_yavas():
    oz = ozet([satir(stt=400), satir(stt=600), satir(t5=False)])
    assert oz['stt']['n'] == 3 and oz['stt']['ort'] == 500
    assert oz['px4']['n'] == 2 and oz['px4']['ort'] == 60
    assert oz['toplam']['n'] == 2
    assert en_yavas(oz) == 'stt'
    assert '| STT' in tablo_md(oz)


def test_eksik_damga_sayilmaz():
    s = satir()
    s['t0'] = s['t1'] = 0          # yazili metin: STT yok
    oz = ozet([s])
    assert oz['stt']['n'] == 0 and oz['toplam']['n'] == 0 and oz['parser']['n'] == 1


def test_kaynaga_gore():
    g = kaynaga_gore([satir(), satir(kaynak='llm', llm=1000)])
    assert set(g) == {'hizli_yol', 'llm'}
    assert g['llm']['parser']['ort'] > 1000


def test_csv_ve_ozet_komutu(tmp_path, capsys):
    yol = tmp_path / 'g.csv'
    with open(yol, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CSV_ALANLARI)
        w.writeheader()
        w.writerow(satir())
        w.writerow(satir(kaynak='llm', llm=900))
    assert csv_oku(yol)[0]['t5'] > 0
    tablo = tmp_path / 'notlar.md'
    assert main([str(yol), '--tablo', str(tablo), '--etiket', 'test']) == 0
    cikti = tablo.read_text()
    assert 'En yavaş aşama' in cikti and '| llm |' in cikti
