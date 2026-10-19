"""LLM'i taklit ederek hattin tamamini (normalize -> acil -> hizli yol -> LLM) dener."""
import json

from command_parser.komut_cozucu import KomutCozucu
from command_parser.llm_client import LLMIstemcisi


class SahteYanit:
    def __init__(self, icerik, durum=200):
        self.icerik = icerik
        self.status_code = durum

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return {'choices': [{'message': {'content': self.icerik}}]}


class SahteOturum:
    def __init__(self, cevaplar):
        self.cevaplar = cevaplar
        self.istekler = []

    def post(self, url, json=None, timeout=None):
        self.istekler.append(json)
        metin = json['messages'][1]['content']
        return SahteYanit(self.cevaplar.get(metin, '{"adimlar":[{"komut":"bilinmiyor"}]}'))

    def get(self, url, timeout=None):
        return SahteYanit('', 200)


IKI_ADIM = json.dumps({'adimlar': [{'komut': 'yuksel', 'metre': 20},
                                   {'komut': 'git_yon', 'yon': 'kuzey', 'metre': 50}]})


def cozucu(cevaplar=None):
    oturum = SahteOturum(cevaplar or {})
    return KomutCozucu(LLMIstemcisi(oturum=oturum)), oturum


def test_istek_ayarlari():
    govde = LLMIstemcisi(oturum=SahteOturum({})).istek_govdesi('kalk')
    assert govde['temperature'] == 0
    assert govde['max_tokens'] == 64
    assert govde['cache_prompt'] is True
    assert govde['response_format']['type'] == 'json_schema'
    assert govde['chat_template_kwargs'] == {'enable_thinking': False}


def test_cok_adim_llm_den():
    c, oturum = cozucu({'önce 20 m yüksel sonra kuzeye 50 m git': IKI_ADIM})
    sonuc = c.coz('önce 20 metre yüksel sonra kuzeye 50 metre git')
    assert sonuc.kaynak == 'llm'
    assert [a['komut'] for a in sonuc.adimlar] == ['yuksel', 'git_yon']
    assert len(oturum.istekler) == 1


def test_dur_llm_e_gitmez():
    c, oturum = cozucu()
    sonuc = c.coz('DUR!')
    assert sonuc.kaynak == 'acil' and sonuc.adimlar == [{'komut': 'dur'}]
    assert oturum.istekler == []


def test_hizli_yol_llm_e_gitmez():
    c, oturum = cozucu()
    assert c.coz('500 metre yüksel').kaynak == 'hizli_yol'
    assert oturum.istekler == []


def test_bilinmiyor_komut_uretmez():
    c, _ = cozucu()
    sonuc = c.coz('bugün hava nasıl')
    assert not sonuc.komut_var and sonuc.kaynak == 'llm'


def test_think_artigi_ve_bozuk_json():
    c, _ = cozucu({'a': '<think>\n\n</think>\n{"adimlar":[{"komut":"in"}]}', 'b': 'merhaba'})
    assert c.coz('a').adimlar == [{'komut': 'in'}]
    sonuc = c.coz('b')
    assert not sonuc.komut_var and 'gecersiz' in sonuc.hata


def test_sonra_ile_baslayan_kuyruga_eklenir():
    c, _ = cozucu()
    sonuc = c.coz('sonra eve dön')
    assert sonuc.kuyruga_ekle and sonuc.adimlar == [{'komut': 'eve_don'}]


def test_onbellek():
    c, oturum = cozucu({'önce 20 m yüksel sonra kuzeye 50 m git': IKI_ADIM})
    c.coz('önce 20 metre yüksel sonra kuzeye 50 metre git')
    sonuc = c.coz('Önce 20 metre yüksel, sonra kuzeye 50 metre git.')
    assert sonuc.kaynak == 'onbellek' and len(oturum.istekler) == 1


def test_llm_yoksa_hizli_yol_calisir():
    c = KomutCozucu(llm=None)
    assert c.coz('kalk').komut_var
    assert not c.coz('önce kalk sonra in').komut_var
