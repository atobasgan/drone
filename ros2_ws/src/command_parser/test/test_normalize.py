"""Gorev 2.1: en az 40 ornekli normalizasyon testi."""
import pytest

from command_parser.normalize import normalize, tr_kucuk

ORNEKLER = [
    # yol haritasindaki kontrol ornegi
    ('Beş Yüz Metre Yüksel!', '500 m yüksel'),
    # sayilar
    ('beş yüz', '500'),
    ('yüz elli', '150'),
    ('bin iki yüz', '1200'),
    ('bir buçuk', '1.5'),
    ('iki buçuk metre', '2.5 m'),
    ('on beş', '15'),
    ('doksan dokuz', '99'),
    ('üç yüz yirmi yedi', '327'),
    ('iki bin beş yüz', '2500'),
    ('bin', '1000'),
    ('yüz', '100'),
    ('sıfır', '0'),
    ('yarım metre', '0.5 m'),
    ('5 yüz metre', '500 m'),
    ('1,5 metre', '1.5 m'),
    ('12.5 metre', '12.5 m'),
    # ekli sayilar
    ('yüz elliye çık', "150'ye çık"),
    ('elliye çık', "50'ye çık"),
    ('dörde', "4'e"),
    ('otuz beşe', "35'e"),
    ('yüzden', "100'den"),
    # belirsiz kelimeler sayi olmamali
    ('bir şey söyle', 'bir şey söyle'),
    ('ona git', 'ona git'),
    ('bir saniye bekle', '1 saniye bekle'),
    ('bir metre in', '1 m in'),
    # birimler
    ('500 metre', '500 m'),
    ('500 mt', '500 m'),
    ('500 m.', '500 m'),
    ('500m yüksel', '500 m yüksel'),
    ('500metre yüksel', '500 m yüksel'),
    ('yüz metreye çık', "100 m'ye çık"),
    ('100 metrede dur', "100 m'de dur"),
    ('2 km kuzeye git', '2000 m kuzeye git'),
    ('iki kilometre ileri', '2000 m ileri'),
    ('bir buçuk km', '1500 m'),
    ('sağa doksan derece dön', 'sağa 90 ° dön'),
    ('90° sağa dön', '90 ° sağa dön'),
    ('kırk beş dereceye dön', '45 ° dön'),
    ('5 sn bekle', '5 saniye bekle'),
    # zaman ve hiz: carpma/bolme LLM'e birakilmaz (Faz 4)
    ('bir dakika bekle', '60 saniye bekle'),
    # "bir elli metre" = "bi elli": yaklasik 50, 51 DEGIL (51 = "elli bir")
    ('bir elli metre yüksel', 'bir 50 m yüksel'),
    ('bir yirmiye çık', "bir 20'ye çık"),
    ('elli bir metre', '51 m'),
    # "ondan sonra" baglactir, 10'dan sonra degil; Whisper'in "meter" yazimi da birimdir
    ('ondan sonra on metre alçal', 'ondan sonra 10 m alçal'),
    ('onda bekle', 'onda bekle'),
    ('on metreden sonra', "10 m'den sonra"),
    ('elli meter yüksel', '50 m yüksel'),
    ('50 metve git', '50 m git'),
    ('mete bey geldi', 'mete bey geldi'),
    ('bir metre', '1 m'),
    ('iki buçuk dakika bekle', '150 saniye bekle'),
    ('yarım dakika bekle', '30 saniye bekle'),
    ('hızı 36 km/saat yap', 'hızı 10 m s yap'),
    ('saatte 18 kilometre ile git', '5 m s ile git'),
    ('hızını beş metre bölü saniye yap', 'hızını 5 m saniye yap'),
    ('bir saat sonra', 'bir saat sonra'),
    ('20 metro yüksel', '20 m yüksel'),
    ('metro istasyonu', 'metro istasyonu'),
    # harf ve noktalama
    ('IŞIK', 'ışık'),
    ('İNİŞ YAP', 'iniş yap'),
    ('Kalk!!!', 'kalk'),
    ('önce 20 metre yüksel, sonra kuzeye 50 metre git.',
     'önce 20 m yüksel sonra kuzeye 50 m git'),
    ('  çok   boşluklu    cümle  ', 'çok boşluklu cümle'),
    ('drone’un', "drone'un"),
    ('', ''),
]


@pytest.mark.parametrize('girdi,beklenen', ORNEKLER)
def test_normalize(girdi, beklenen):
    assert normalize(girdi) == beklenen


def test_en_az_40_ornek():
    assert len(ORNEKLER) >= 40


def test_tr_kucuk():
    assert tr_kucuk('ISPARTA İZMİR') == 'ısparta izmir'
