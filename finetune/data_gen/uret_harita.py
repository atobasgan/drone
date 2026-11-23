"""Gorev 5.4 veri seti: Faz 4 verisi AYNEN + yere_git ornekleri -> finetune/data_faz5/

    python3 -m finetune.data_gen.uret_harita            # depo kokunden
    python3 -m finetune.data_gen.uret_harita --dogrula  # + genis sema ile denetle

Faz 4'un uret.py'si ve data/ klasoru DEGISMEZ. Burada:
  1. data/{train,val,test}.jsonl okunur, oldugu gibi kopyalanir (eski test seti ayni kalir:
     Faz 4 modeliyle ayni cumlelerde karsilastirilabilir, gerileme olculur).
  2. yer adlari ve sablonlar train/val/test'e ayrilir (harita_sablonlari.py)
  3. tek adim "X'e git", cok adim "kalkıp X'e git", "X'e gidip in", STT bicimi ("anıtkabire")
  4. "bir yere git" turu negatifler
  5. kontrol: genis sema (yere_git dahil), ad cumlede geciyor, sayi/acil kurallari (kontrol.py)
Ayni tohumla her calistirma ayni veriyi uretir.
"""
import argparse
from collections import Counter
import os
import random

from . import cesitleme, sablonlar
from ..ortak import FINETUNE, VERI, el_yazisi_cumleler, jsonl_oku, jsonl_yaz, normalize, sohbet_ornegi
from .doldur import doldur
from .harita_sablonlari import HARITA_NEGATIFLERI, YER_ADLARI, YERE_GIT_SABLONLARI, YERE_GIT_ULAC, yonelme
from .kontrol import ACIL_KELIMELER, _sayi_mi, sorun

from command_parser.harita_komutlari import dogrula_genis  # noqa: E402 (yolu ortak ekler)

VERI_FAZ5 = os.path.join(FINETUNE, 'data_faz5')
BOLUMLER = ('train', 'val', 'test')
ORAN = {'train': 1.0, 'val': 0.15, 'test': 0.25}
# yere_git ile birlesecek Faz 4 komutlari (dur acil yoldan gider, yakin_yere_git karisiklik yaratir)
ESLER = ('kalk', 'in', 'yuksel', 'alcal', 'irtifaya_cik', 'don', 'bekle', 'hiz_ayarla', 'eve_don')


# ------------------------------------------------------------------ 1. bol
def bol(rng, liste, val=0.15, test=0.2):
    liste = list(liste)
    rng.shuffle(liste)
    n_test, n_val = max(1, round(len(liste) * test)), max(1, round(len(liste) * val))
    return {'test': liste[:n_test], 'val': liste[n_test:n_test + n_val], 'train': liste[n_test + n_val:]}


# ------------------------------------------------------------------ 2. ornekler
def yere_git_parcasi(rng, sablon, ad):
    ad = normalize(ad)
    return sablon.format(yer=ad, yer_e=yonelme(ad)), {'komut': 'yere_git', 'ad': ad}


def tek_adimlar(rng, sablonlar_, adlar, adet):
    ornekler = []
    for i in range(adet):
        cumle, adim = yere_git_parcasi(rng, rng.choice(sablonlar_), adlar[i % len(adlar)])
        if rng.random() < 0.2:
            cumle = cesitleme.dolgu_ekle(rng, cumle)
        ornekler.append({'cumle': cumle, 'adimlar': [adim], 'kaynak': 'harita', 'sablon': 'harita:tek'})
    return ornekler


def _es(rng, bolum_sablonlari):
    komut = rng.choice(ESLER)
    return doldur(rng, rng.choice(bolum_sablonlari[komut]), komut) + (komut,)


def cok_adimlar(rng, sablonlar_, adlar, bolum_sablonlari, adet):
    """'kalkıp anıtkabir'e git', 'önce 30 metreye çık sonra X'e uç', 'X'e gidip in'."""
    ornekler = []
    for _ in range(adet):
        ad = rng.choice(adlar)
        es_cumle, es_adim, es_komut = _es(rng, bolum_sablonlari)
        bicim = rng.random()
        if bicim < 0.3 and es_komut in sablonlar.ULAC_ILK:           # "kalkıp X'e git"
            ulac, es_adim = doldur(rng, rng.choice(sablonlar.ULAC_ILK[es_komut]), es_komut)
            yer_cumle, yer_adim = yere_git_parcasi(rng, rng.choice(sablonlar_), ad)
            cumle, adimlar = f'{ulac} {yer_cumle}', [es_adim, yer_adim]
        elif bicim < 0.5:                                            # "X'e gidip in"
            yer_cumle, yer_adim = yere_git_parcasi(rng, rng.choice(YERE_GIT_ULAC), ad)
            cumle, adimlar = f'{yer_cumle} {es_cumle}', [yer_adim, es_adim]
        elif bicim < 0.75:                                           # "önce A sonra X'e git"
            yer_cumle, yer_adim = yere_git_parcasi(rng, rng.choice(sablonlar_), ad)
            cumle, adimlar = f'önce {es_cumle} sonra {yer_cumle}', [es_adim, yer_adim]
        else:                                                        # "X'e git ve A"
            yer_cumle, yer_adim = yere_git_parcasi(rng, rng.choice(sablonlar_), ad)
            cumle, adimlar = f'{yer_cumle} {rng.choice(sablonlar.BAGLACLAR)} {es_cumle}', [yer_adim, es_adim]
        ornekler.append({'cumle': cumle, 'adimlar': adimlar, 'kaynak': 'harita_cok', 'sablon': 'harita:cok'})
    return ornekler


def stt_bicimi(rng, ornekler, oran):
    """Whisper cogu zaman kesme isaretini yazmaz: "anıtkabir'e" -> "anıtkabire". Etiket ayni."""
    kopyalar = []
    for o in ornekler:
        if "'" in o['cumle'] and rng.random() < oran:
            kopyalar.append({**o, 'cumle': o['cumle'].replace("'", ''), 'gurultu': 'kesme'})
    return kopyalar


def negatifler(cumleler):
    return [{'cumle': c, 'adimlar': [{'komut': 'bilinmiyor'}], 'kaynak': 'negatif:harita',
             'sablon': f'negatif:{c}'} for c in cumleler]


# ------------------------------------------------------------------ 3. kontrol
def harita_sorun(norm, adimlar):
    """kontrol.sorun'un yere_git'i de taniyan hali. Sorun yoksa None."""
    try:
        dogrula_genis({'adimlar': adimlar})
    except ValueError as e:
        return f'sema: {e}'
    for a in adimlar:
        if a['komut'] == 'yere_git' and a['ad'] not in norm:
            return 'ad cumlede yok'
    digerleri = [a for a in adimlar if a['komut'] != 'yere_git']
    if digerleri:
        return sorun(norm, digerleri)            # sayi ve acil kelime kurallari aynen
    if normalize(norm) != norm:
        return 'normalize tekrar uygulaninca degisiyor'
    if any(_sayi_mi(t) for t in norm.replace("'", ' ').split()):
        return 'etikette olmayan sayi'
    if not ACIL_KELIMELER.isdisjoint(norm.split()):
        return "acil kelime var (LLM'e gitmez)"
    return None


def temizle(ornekler, yasakli, gorulen, sayac):
    temiz = []
    for o in ornekler:
        norm = normalize(o['cumle'])
        neden = harita_sorun(norm, o['adimlar']) if norm else 'bos'
        if neden is None and norm in yasakli:
            neden = 'elle yazilmis test setinde var'
        if neden is None and norm in gorulen:
            neden = 'tekrar ya da baska bolumde var'
        if neden:
            sayac[neden.split(':')[0]] += 1
            continue
        gorulen.add(norm)
        temiz.append({**o, 'norm': norm})
    return temiz


def satir(o):
    return sohbet_ornegi(o['norm'], o['adimlar'], ham=o['cumle'], kaynak=o['kaynak'], sablon=o['sablon'],
                         gurultu=o.get('gurultu', ''), komutlar=[a['komut'] for a in o['adimlar']])


# ------------------------------------------------------------------ 4. hepsi
def uret(tohum=42, tek_adet=480, cok_orani=0.3, stt_orani=0.25, eski_veri=VERI):
    """{bolum: (eski_satirlar, yeni_satirlar)}, atilan sayaci."""
    rng = random.Random(tohum)
    adlar = bol(rng, YER_ADLARI)
    sablon_bolumu = bol(rng, YERE_GIT_SABLONLARI)
    negatif_bolumu = bol(rng, HARITA_NEGATIFLERI)
    eski = {b: jsonl_oku(os.path.join(eski_veri, f'{b}.jsonl')) for b in BOLUMLER}
    gorulen = {s['messages'][1]['content'] for b in BOLUMLER for s in eski[b]}
    yasakli = el_yazisi_cumleler()
    atilan = Counter()
    sonuc = {}
    for b in ('test', 'val', 'train'):
        # cok adimin Faz 4 parcasi butun sablonlardan secilir; ayrik olan yer adlari ve yere_git sablonlari
        es_sablonlari = sablonlar.SABLONLAR
        n_tek = max(20, int(tek_adet * ORAN[b]))
        ornekler = tek_adimlar(rng, sablon_bolumu[b], adlar[b], n_tek)
        ornekler += cok_adimlar(rng, sablon_bolumu[b], adlar[b], es_sablonlari, int(n_tek * cok_orani))
        ornekler += stt_bicimi(rng, ornekler, stt_orani)
        ornekler += negatifler(negatif_bolumu[b])
        temiz = temizle(ornekler, yasakli, gorulen, atilan)
        rng.shuffle(temiz)
        sonuc[b] = (eski[b], [satir(o) for o in temiz])
    return sonuc, atilan, adlar


def dagilim_yaz(yol, sonuc, atilan, adlar):
    with open(yol, 'w', encoding='utf-8') as f:
        f.write('# Faz 5 veri dağılımı (Görev 5.4)\n\nÜretim: `python3 -m finetune.data_gen.uret_harita`\n\n'
                'Faz 4 verisi (`finetune/data/`) aynen alınır, üstüne `yere_git` örnekleri eklenir.\n\n'
                '| bölüm | Faz 4 örnek | yeni örnek | yere_git tek | yere_git çok adımlı | kesmesiz (STT) '
                '| negatif | toplam |\n|---|---|---|---|---|---|---|---|\n')
        for b in BOLUMLER:
            eski, yeni = sonuc[b]
            say = Counter(s['meta']['kaynak'] for s in yeni)
            stt = sum(1 for s in yeni if s['meta']['gurultu'])
            f.write(f'| {b} | {len(eski)} | {len(yeni)} | {say["harita"]} | {say["harita_cok"]} | {stt} '
                    f'| {say["negatif:harita"]} | {len(eski) + len(yeni)} |\n')
        f.write('\n## Yer adları (bölümler ayrık: testteki yerler eğitimde hiç geçmez)\n\n')
        for b in BOLUMLER:
            f.write(f'- **{b}** ({len(adlar[b])}): {", ".join(sorted(adlar[b]))}\n')
        f.write('\n## Atılan örnekler (otomatik kontrol)\n\n| neden | adet |\n|---|---|\n')
        for k, n in atilan.most_common():
            f.write(f'| {k} | {n} |\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tohum', type=int, default=42)
    ap.add_argument('--tek-adet', type=int, default=480, help='train için tek adımlı yere_git örneği')
    ap.add_argument('--cikti', default=VERI_FAZ5)
    ap.add_argument('--dogrula', action='store_true', help='yazdıktan sonra tüm satırları geniş şemayla denetle')
    args = ap.parse_args(argv)

    sonuc, atilan, adlar = uret(args.tohum, args.tek_adet)
    for b in BOLUMLER:
        eski, yeni = sonuc[b]
        jsonl_yaz(os.path.join(args.cikti, f'{b}.jsonl'), eski + yeni)
        jsonl_yaz(os.path.join(args.cikti, f'{b}_harita.jsonl'), yeni)      # yalniz yeni ornekler (olcum)
    dagilim_yaz(os.path.join(args.cikti, 'dagilim.md'), sonuc, atilan, adlar)
    print(' | '.join(f'{b}: {len(sonuc[b][0])}+{len(sonuc[b][1])}' for b in BOLUMLER), f'| atılan: {dict(atilan)}')
    if args.dogrula:
        from .dogrula_harita import denetle
        hatalar = denetle(args.cikti)
        for h in hatalar[:20]:
            print('HATA', h)
        print('TÜM KONTROLLER GEÇTİ' if not hatalar else f'{len(hatalar)} hata')
        return 1 if hatalar else 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
