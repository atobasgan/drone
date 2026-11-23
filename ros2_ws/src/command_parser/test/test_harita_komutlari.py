"""Faz 5: yere_git semasi, harita hizli yolu, HaritaLLMIstemcisi (sahte HTTP)."""
import json

import pytest

from command_parser.harita_komutlari import (HARITA_SEMASI, HARITA_SISTEM_PROMPT, HaritaKomutCozucu,
                                             HaritaLLMIstemcisi, dogrula_genis, harita_hizli_yol)
from command_parser.komut_cozucu import KomutCozucu
from command_parser.normalize import normalize
from command_parser.prompt import KISA_SISTEM_PROMPT, SISTEM_PROMPT
from command_parser.schema import KOMUT_SEMASI, SemaHatasi


class Yanit:
    def __init__(self, icerik):
        self.icerik, self.status_code = icerik, 200

    def raise_for_status(self):
        pass

    def json(self):
        return {'choices': [{'message': {'content': self.icerik}}]}


class Oturum:
    def __init__(self, cevaplar):
        self.cevaplar, self.istekler = cevaplar, []

    def post(self, url, json=None, timeout=None):
        self.istekler.append(json)
        return Yanit(self.cevaplar.get(json['messages'][1]['content'], '{"adimlar":[{"komut":"bilinmiyor"}]}'))


@pytest.mark.parametrize('cumle, tur', [
    ('en yakın hastaneye git', 'hastane'), ('bana en yakın eczaneye uç', 'eczane'),
    ('lütfen en yakın benzinliğe git', 'benzinlik'), ('en yakın karakola git', 'polis'),
    ('en yakın parka kadar uç', 'park'), ('hemen en yakın markete git', 'market'),
    ('en yakın okula gidelim', 'okul'),
])
def test_harita_hizli_yol(cumle, tur):
    assert harita_hizli_yol(normalize(cumle)) == [{'komut': 'yakin_yere_git', 'tur': tur}]


@pytest.mark.parametrize('cumle', ['en yakın hastane nerede', 'en yakın kafeye git', 'hastaneye git',
                                   'en yakın hastaneye git sonra in'])
def test_harita_hizli_yol_dar_ve_kesin(cumle):
    assert harita_hizli_yol(normalize(cumle)) is None          # emin degilse LLM'e


def test_cozucu_acil_once_baglac_ve_eski_davranis():
    c = HaritaKomutCozucu()
    s = c.coz('en yakın hastaneye git')
    assert s.kaynak == 'hizli_yol' and s.adimlar == [{'komut': 'yakin_yere_git', 'tur': 'hastane'}]
    s = c.coz('sonra en yakın eczaneye git')
    assert s.kuyruga_ekle and s.adimlar[0]['tur'] == 'eczane'
    assert c.coz('en yakın hastaneye gitme dur').kaynak == 'acil'
    eski = KomutCozucu()                                        # Faz 4'e kadarki davranis aynen
    for cumle in ['kalk', '20 metre yüksel', 'sağa dön', 'bugün hava nasıl', 'beş saniye bekle']:
        a, b = c.coz(cumle), eski.coz(cumle)
        assert (a.adimlar, a.kaynak, a.kuyruga_ekle) == (b.adimlar, b.kaynak, b.kuyruga_ekle)


def test_genis_sema_ve_dogrulama():
    assert len(HARITA_SEMASI['properties']['adimlar']['items']['anyOf']) == \
        len(KOMUT_SEMASI['properties']['adimlar']['items']['anyOf']) + 1      # orijinal sema degismedi
    assert '"yere_git"' not in json.dumps(KOMUT_SEMASI)           # ("yakin_yere_git" baska komut)
    assert dogrula_genis({'adimlar': [{'komut': 'kalk'}, {'komut': 'yere_git', 'ad': ' Anıtkabir '}]}) == \
        [{'komut': 'kalk'}, {'komut': 'yere_git', 'ad': 'Anıtkabir'}]
    for bozuk in [{'adimlar': [{'komut': 'yere_git'}]}, {'adimlar': [{'komut': 'yere_git', 'ad': 'x'}]},
                  {'adimlar': [{'komut': 'yere_git', 'ad': 'Ankara', 'tur': 'park'}]}, {'adimlar': []}]:
        with pytest.raises(SemaHatasi):
            dogrula_genis(bozuk)


def test_few_shot_prompt_genisledi_orijinal_ayni():
    assert 'yere_git {ad}' in HARITA_SISTEM_PROMPT and '"komut":"yere_git"' in HARITA_SISTEM_PROMPT
    assert 'yere_git {ad}' not in SISTEM_PROMPT and HARITA_SISTEM_PROMPT.endswith('/no_think')


def test_harita_llm_istemcisi():
    yere = '{"adimlar":[{"komut":"yere_git","ad":"Anıtkabir"}]}'
    o = Oturum({"anıtkabir'e uç": yere, 'a': '{"adimlar":[{"komut":"in"}]}',
                'b': '{"adimlar":[{"komut":"yere_git","ad":"A"},{"komut":"yere_git","ad":"A"},'
                     '{"komut":"yere_git","ad":"A"}]}'})
    llm = HaritaLLMIstemcisi(oturum=o)
    assert llm.sistem_prompt == HARITA_SISTEM_PROMPT and llm.sema is HARITA_SEMASI
    assert llm.cevir("anıtkabir'e uç").adimlar == [{'komut': 'yere_git', 'ad': 'Anıtkabir'}]
    assert llm.cevir('a').adimlar == [{'komut': 'in'}]
    assert not llm.cevir('b').basarili                         # tekrar dongusu yine reddedilir
    kisa = HaritaLLMIstemcisi(oturum=o, sistem_prompt=KISA_SISTEM_PROMPT)
    assert kisa.sistem_prompt == KISA_SISTEM_PROMPT            # fine-tune'lu modelin prompt'u aynen
    assert '"yere_git"' in json.dumps(o.istekler[0]['response_format'])
