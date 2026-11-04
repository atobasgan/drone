# stt_node -> command_parser. Taninan metin + Faz 3 zaman damgalari (MIMARI 9.3).
# Terminal / telefondan gelen duz metin icin /voice/text (std_msgs/String) aynen calisir.
string metin                               # STT ham ciktisi (normalizasyonu parser yapar)
string kaynak                              # mikrofon | dosya | telefon
string dosya                               # dosya modunda WAV yolu (test eslestirmesi icin)
builtin_interfaces/Time t_konusma_bitti    # t0: VAD konusma bitti (dosya modunda: dosya alindi)
builtin_interfaces/Time t_stt_bitti        # t1: STT cikti verdi
float32 konusma_s                          # konusma parcasinin uzunlugu
