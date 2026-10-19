"""Komutlar icin kullaniciya donulecek Turkce geri bildirim cumleleri."""

YON_ADLARI = {
    'ileri': 'ileri', 'geri': 'geri', 'sag': 'sağa', 'sol': 'sola',
    'kuzey': 'kuzeye', 'guney': 'güneye', 'dogu': 'doğuya', 'bati': 'batıya',
}


def _s(deger):
    """12.0 -> '12', 1.5 -> '1.5'"""
    return f'{float(deger or 0):g}'


def baslarken(komut):
    ad = komut.get('komut')
    m = komut.get('metre') or 0
    if ad == 'kalk':
        return f'{_s(m)} metreye kalkıyorum' if m else 'kalkıyorum'
    if ad == 'yuksel':
        return f'{_s(m)} metre yükseliyorum'
    if ad == 'alcal':
        return f'{_s(m)} metre alçalıyorum'
    if ad == 'irtifaya_cik':
        return f'{_s(m)} metre irtifaya gidiyorum'
    if ad == 'git_yon':
        return f'{YON_ADLARI.get(komut.get("yon"), komut.get("yon"))} {_s(m)} metre gidiyorum'
    if ad == 'don':
        yon = YON_ADLARI.get(komut.get('yon'), komut.get('yon'))
        return f'{yon} {_s(komut.get("derece"))} derece dönüyorum'
    if ad == 'git_koordinat':
        return f'{komut.get("enlem"):.5f}, {komut.get("boylam"):.5f} koordinatına gidiyorum'
    if ad == 'bekle':
        return f'{_s(komut.get("saniye"))} saniye bekliyorum'
    if ad == 'hiz_ayarla':
        return f'hızı {_s(komut.get("mps"))} m/s yaptım'
    if ad == 'eve_don':
        return 'eve dönüyorum'
    if ad == 'in':
        return 'iniyorum'
    if ad == 'dur':
        return 'duruyorum'
    return ad or ''
