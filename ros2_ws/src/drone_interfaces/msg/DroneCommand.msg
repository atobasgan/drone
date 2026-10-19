# Tek bir drone komutu. LLM / hizli yol ile yurutucu arasindaki "sozlesme".
# Kullanilmayan alanlar 0 / bos birakilir. Komut listesi icin MIMARI.txt Bolum 4.
#
# komut: kalk, in, yuksel, alcal, irtifaya_cik, git_yon, don, git_koordinat,
#        yakin_yere_git, bekle, hiz_ayarla, eve_don, dur
string komut

float32 metre      # yuksel/alcal/irtifaya_cik/git_yon mesafesi; kalk ve
                   # git_koordinat icin hedef irtifa (0 = varsayilan/mevcut)
float32 derece     # don
string yon         # git_yon: ileri|geri|sag|sol|kuzey|guney|dogu|bati
                   # don    : sag|sol
float64 enlem      # git_koordinat
float64 boylam     # git_koordinat
string tur         # yakin_yere_git: hastane|eczane|benzinlik|...
float32 saniye     # bekle
float32 mps        # hiz_ayarla (m/s)
