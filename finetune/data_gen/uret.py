"""Faz 4 veri seti: train.jsonl / val.jsonl / test.jsonl + dagilim.md

    python3 -m finetune.data_gen.uret                     # depo kokunden
    python3 -m finetune.data_gen.uret --ek-veri stt.jsonl # gercek STT ciktilari (yalniz train)

Akis (her adim ayri fonksiyon):
  1. sablonlari_bol      : her komutun sablonlari train/val/test'e AYRILIR (Gorev 4.3:
                           ayni sablondan turemis cumleler iki tarafa dusmesin)
  2. tek_adimlar         : sablon x rastgele parametre               (Gorev 4.1, 4.2)
  3. cok_adimlar         : 2-3 komut "önce/sonra/ve/ardından" ya da ulacla
  4. negatifler          : "bilinmiyor" ornekleri, %10-15             (Gorev 4.3)
  5. gurultulu_kopyalar  : orneklerin bir kismina STT hata taklidi    (Gorev 4.3)
  6. temizle             : normalize, otomatik kontrol, tekrar ve sizinti temizligi
  7. yaz                 : chat-JSONL + dagilim tablosu
Ayni tohumla her calistirma ayni veriyi uretir.
"""
import argparse
from collections import Counter, defaultdict
import os
import random

from . import cesitleme, ek_sablonlar, negatifler, sablonlar, stt_gurultusu
from ..ortak import KOK, VERI, el_yazisi_cumleler, jsonl_oku, jsonl_yaz, normalize, sohbet_ornegi
from .doldur import bosluklar, doldur
from .kontrol import sorun

BOLUMLER = ('train', 'val', 'test')
COK_ADIMA_GIRMEYEN = {'dur'}          # "dur" zaten acil yoldan gider
# Gorev 4.6 ikinci tur: "kalkıp 60 saniye bekle" -> kalk irtifa 60 hatasi icin bu komutlar
# cok adimli cumlenin ILK adimi olarak daha sik secilir (sayisiz ilk adim + sayili ikinci adim).
ILK_ADIM_KOMUTLARI = ('kalk', 'don', 'in', 'eve_don')
# Kullanimda nadir ama parametresi cok (uzun koordinat) komutun payi dusuk tutulur.
KOMUT_AGIRLIK = {'git_koordinat': 0.4}


# ------------------------------------------------------------------ 1. sablonlari bol
def sablonlari_bol(rng, val_orani=0.1, test_orani=0.1, ek=True):
    """{bolum: [(kaynak, komut, sablon, sablon_id), ...]}. Her komuttan her bolume en az 1.
    ek=True: ek_sablonlar.py (ikinci tur) karistirmaya girmeden yalniz train'e eklenir."""
    bolum = defaultdict(list)
    for kaynak, sozluk in (('sablon', sablonlar.SABLONLAR), ('cesitleme', cesitleme.CESITLEME)):
        for komut, liste in sozluk.items():
            girdiler = [(kaynak, komut, s, f'{kaynak}:{komut}:{i}') for i, s in enumerate(liste)]
            rng.shuffle(girdiler)
            n_test = max(1, round(len(girdiler) * test_orani))
            n_val = max(1, round(len(girdiler) * val_orani))
            bolum['test'] += girdiler[:n_test]
            bolum['val'] += girdiler[n_test:n_test + n_val]
            bolum['train'] += girdiler[n_test + n_val:]
    if ek:
        for komut, liste in ek_sablonlar.EK_SABLONLAR.items():
            bolum['train'] += [('ek_sablon', komut, s, f'ek_sablon:{komut}:{i}') for i, s in enumerate(liste)]
    return bolum


# ------------------------------------------------------------------ 2. tek adim
def tek_adimlar(rng, girdiler, komut_basina):
    """Her komuttan yaklasik komut_basina ornek. Parametresiz sablon az tekrar eder."""
    komut_sablonlari = defaultdict(list)
    for g in girdiler:
        komut_sablonlari[g[1]].append(g)
    ornekler = []
    for komut, liste in komut_sablonlari.items():
        hedef = int(komut_basina * KOMUT_AGIRLIK.get(komut, 1.0))
        tekrar = max(1, -(-hedef // len(liste)))                   # yukari yuvarlanmis bolum
        for kaynak, _, sablon, sid in liste:
            # parametresiz sablon ("eve dön") ancak dolgu sozuyle cesitlenebilir
            n = tekrar if bosluklar(sablon) else min(tekrar, 6)
            for j in range(n):
                cumle, adim = doldur(rng, sablon, komut)
                if j > 0 and not bosluklar(sablon):
                    cumle = cesitleme.dolgu_ekle(rng, cumle)
                ornekler.append({'cumle': cumle, 'adimlar': [adim], 'kaynak': kaynak, 'sablon': sid})
    return ornekler


# ------------------------------------------------------------------ 3. cok adim
def _parca(rng, girdiler, komut=None):
    adaylar = [g for g in girdiler if g[1] not in COK_ADIMA_GIRMEYEN and (komut is None or g[1] == komut)]
    kaynak, k, sablon, sid = rng.choice(adaylar)
    cumle, adim = doldur(rng, sablon, k)
    return cumle, adim, sid


def cok_adimlar(rng, girdiler, adet, ilk_adim_orani=0.0):
    """"önce A sonra B", "A ve B", "A ardından B sonra C", "A-ıp B" (ulac)."""
    ornekler = []
    for _ in range(adet):
        n = 3 if rng.random() < 0.25 else 2
        ilk = None
        if ilk_adim_orani and rng.random() < ilk_adim_orani:       # oran 0 iken rng'ye dokunma:
            ilk = rng.choice(ILK_ADIM_KOMUTLARI)                   # test/val birebir ayni kalmali
        parcalar = [_parca(rng, girdiler, ilk)] + [_parca(rng, girdiler) for _ in range(n - 1)]
        cumleler = [c for c, _, _ in parcalar]
        adimlar = [a for _, a, _ in parcalar]
        bicim = rng.random()
        if bicim < 0.25:
            cumle = f'önce {cumleler[0]} sonra ' + ' sonra '.join(cumleler[1:])
        elif bicim < 0.4 and adimlar[0]['komut'] in sablonlar.ULAC_ILK:
            ilk, adim0 = doldur(rng, rng.choice(sablonlar.ULAC_ILK[adimlar[0]['komut']]), adimlar[0]['komut'])
            adimlar[0] = adim0
            cumle = ' '.join([ilk] + cumleler[1:])
        else:
            cumle = cumleler[0]
            for c in cumleler[1:]:
                cumle += f' {rng.choice(sablonlar.BAGLACLAR)} {c}'
        ornekler.append({'cumle': cumle, 'adimlar': adimlar, 'kaynak': 'cok_adim',
                         'sablon': '+'.join(s for _, _, s in parcalar)})
    return ornekler


# ------------------------------------------------------------------ 4. negatifler
def negatif_bolumleri(rng, ek=True):
    """Negatif cumleler de cumle bazinda bolunur (ayni cumle iki tarafa dusmesin)."""
    hepsi = negatifler.hepsi()
    rng.shuffle(hepsi)
    n = len(hepsi)
    bolum = {'test': hepsi[:n // 10], 'val': hepsi[n // 10:n // 5], 'train': hepsi[n // 5:]}
    if ek:
        bolum['train'] = bolum['train'] + [(c, 'ek') for c in ek_sablonlar.EK_NEGATIFLER]
    return bolum


def negatif_ornekler(rng, cumleler, adet):
    ornekler = []
    for i in range(adet):
        cumle, grup = cumleler[i % len(cumleler)]
        if i >= len(cumleler):               # tekrar ederken dolgu ya da STT bicimiyle cesitle
            cumle = cesitleme.dolgu_ekle(rng, cumle) if rng.random() < 0.7 else \
                stt_gurultusu.gurultu_ekle(rng, cumle)[0]
        ornekler.append({'cumle': cumle, 'adimlar': [{'komut': 'bilinmiyor'}],
                         'kaynak': f'negatif:{grup}', 'sablon': f'negatif:{cumle}'})
    return ornekler


# ------------------------------------------------------------------ 5. STT gurultusu
def gurultulu_kopyalar(rng, ornekler, oran):
    kopyalar = []
    for o in ornekler:
        if o['adimlar'][0]['komut'] == 'bilinmiyor' or rng.random() >= oran:
            continue
        cumle, uygulanan = stt_gurultusu.gurultu_ekle(rng, o['cumle'])
        if uygulanan and cumle != o['cumle']:
            kopyalar.append({**o, 'cumle': cumle, 'gurultu': '+'.join(uygulanan)})
    return kopyalar


# ------------------------------------------------------------------ 6. temizle
def temizle(ornekler, yasakli, onceki_bolumler, sayac):
    """normalize + kontrol + tekrar temizligi.
    yasakli: elle yazilmis test cumleleri; onceki_bolumler: test/val'de gecen cumleler."""
    gorulen, temiz = set(), []
    for o in ornekler:
        norm = normalize(o['cumle'])
        neden = sorun(norm, o['adimlar']) if norm else 'bos'
        if neden is None and norm in yasakli:
            neden = 'elle yazilmis test setinde var'
        if neden is None and norm in onceki_bolumler:
            neden = 'baska bolumde var'
        if neden is None and norm in gorulen:
            neden = 'tekrar'
        if neden:
            sayac[neden.split(':')[0]] += 1
            continue
        gorulen.add(norm)
        temiz.append({**o, 'norm': norm})
    return temiz


# ------------------------------------------------------------------ 7. yaz
def satir(o):
    return sohbet_ornegi(o['norm'], o['adimlar'], ham=o['cumle'], kaynak=o['kaynak'],
                         sablon=o['sablon'], gurultu=o.get('gurultu', ''),
                         komutlar=[a['komut'] for a in o['adimlar']])


def dagilim_yaz(yol, bolumler, atilan, args):
    komutlar = sorted({a['komut'] for b in bolumler.values() for o in b for a in o['adimlar']})
    with open(yol, 'w', encoding='utf-8') as f:
        f.write('# Faz 4 veri dağılımı\n\n')
        secenekler = f'--tohum {args.tohum} --komut-basina {args.komut_basina}'
        secenekler += ''.join(f' --ek-veri {os.path.relpath(y, KOK)}' for y in args.ek_veri)
        secenekler += ' --ilk-tur' if args.ilk_tur else ''
        f.write(f'Üretim: `python3 -m finetune.data_gen.uret {secenekler}`\n\n')
        f.write('| bölüm | örnek | tek adım | çok adımlı | negatif | STT gürültülü | ek veri |\n')
        f.write('|---|---|---|---|---|---|---|\n')
        for ad in BOLUMLER:
            b = bolumler[ad]
            say = Counter('negatif' if o['kaynak'].startswith('negatif') else
                          'cok' if len(o['adimlar']) > 1 else 'tek' for o in b)
            gurultulu = sum(1 for o in b if o.get('gurultu'))
            ek = sum(1 for o in b if o['kaynak'] == 'ek')
            f.write(f'| {ad} | {len(b)} | {say["tek"]} | {say["cok"]} | {say["negatif"]} | {gurultulu} | {ek} |\n')
        f.write('\n## Komut dağılımı (adım sayısı)\n\n| komut | ' + ' | '.join(BOLUMLER) + ' |\n')
        f.write('|---|' + '---|' * len(BOLUMLER) + '\n')
        for k in komutlar:
            sayilar = [sum(1 for o in bolumler[b] for a in o['adimlar'] if a['komut'] == k) for b in BOLUMLER]
            f.write(f'| {k} | ' + ' | '.join(map(str, sayilar)) + ' |\n')
        f.write('\n## Kaynak dağılımı (train)\n\n| kaynak | örnek |\n|---|---|\n')
        for k, n in Counter(o['kaynak'] for o in bolumler['train']).most_common():
            f.write(f'| {k} | {n} |\n')
        f.write('\n## Atılan örnekler (otomatik kontrol)\n\n| neden | adet |\n|---|---|\n')
        for k, n in atilan.most_common():
            f.write(f'| {k} | {n} |\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tohum', type=int, default=42)
    ap.add_argument('--komut-basina', type=int, default=260, help='her komuttan tek adımlı örnek (train)')
    ap.add_argument('--cok-adim-orani', type=float, default=0.17)
    ap.add_argument('--negatif-orani', type=float, default=0.12)
    ap.add_argument('--gurultu-orani', type=float, default=0.35, help='gürültülü kopyası eklenecek oran')
    ap.add_argument('--ek-veri', action='append', default=[],
                    help='{"metin","beklenen"} JSONL; YALNIZ train\'e eklenir (gerçek STT çıktıları)')
    ap.add_argument('--ilk-adim-orani', type=float, default=0.3,
                    help='çok adımlıda ilk adımın kalk/don/in/eve_don olma oranı (4.6 ikinci tur)')
    ap.add_argument('--ilk-tur', action='store_true',
                    help='4.6 öncesi veri: ek_sablonlar.py ve ilk adım ağırlığı yok (ilk modelin verisi)')
    ap.add_argument('--cikti', default=VERI)
    args = ap.parse_args(argv)

    rng = random.Random(args.tohum)
    ek = not args.ilk_tur
    sablon_bolumleri = sablonlari_bol(rng, ek=ek)
    negatif_bolumu = negatif_bolumleri(rng, ek=ek)
    ilk_adim_orani = args.ilk_adim_orani if ek else 0.0
    yasakli = el_yazisi_cumleler()
    atilan = Counter()
    bolumler = {}
    gorulen = set()
    for ad in ('test', 'val', 'train'):     # test once: ayni cumle train'de cikarsa train'den atilir
        olcek = 1.0 if ad == 'train' else 0.25        # val/test daha kucuk (~%10'ar)
        tek = tek_adimlar(rng, sablon_bolumleri[ad], max(4, int(args.komut_basina * olcek)))
        n_cok = int(len(tek) * args.cok_adim_orani / (1 - args.cok_adim_orani))
        cok = cok_adimlar(rng, sablon_bolumleri[ad], n_cok, ilk_adim_orani if ad == 'train' else 0.0)
        ornekler = tek + cok
        ornekler += gurultulu_kopyalar(rng, ornekler, args.gurultu_orani)
        n_neg = int(len(ornekler) * args.negatif_orani / (1 - args.negatif_orani))
        ornekler += negatif_ornekler(rng, negatif_bolumu[ad], n_neg)
        if ad == 'train':
            for yol in args.ek_veri:
                ornekler += [{'cumle': o['metin'], 'adimlar': o['beklenen']['adimlar'], 'kaynak': 'ek',
                              'sablon': f'ek:{os.path.basename(yol)}'} for o in jsonl_oku(yol)]
        temiz = temizle(ornekler, yasakli, gorulen, atilan)
        gorulen |= {o['norm'] for o in temiz}
        rng.shuffle(temiz)
        bolumler[ad] = temiz

    for ad in BOLUMLER:
        jsonl_yaz(os.path.join(args.cikti, f'{ad}.jsonl'), [satir(o) for o in bolumler[ad]])
    dagilim_yaz(os.path.join(args.cikti, 'dagilim.md'), bolumler, atilan, args)
    print(' | '.join(f'{ad}: {len(bolumler[ad])}' for ad in BOLUMLER), f'| atılan: {dict(atilan)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
