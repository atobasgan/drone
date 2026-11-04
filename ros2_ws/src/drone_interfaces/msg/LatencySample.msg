# mission_executor -> latency_monitor. Bir komutun asama asama zaman damgalari (MIMARI 9.3).
# Olmayan damga 0 kalir: terminalden gelen komutta t0/t1, hareket ettirmeyen komutta t5.
string metin
string kaynak          # acil | hizli_yol | onbellek | llm | terminal
string ses_kaynagi     # mikrofon | dosya | telefon | bos (yazili metin)
string sonuc           # kabul | kuyrukta | reddedildi
builtin_interfaces/Time t0_konusma_bitti
builtin_interfaces/Time t1_stt_bitti
builtin_interfaces/Time t_metin_geldi
builtin_interfaces/Time t2_komut_hazir
builtin_interfaces/Time t3_yurutucu_aldi
builtin_interfaces/Time t4_ilk_setpoint
builtin_interfaces/Time t5_hiz_degisti
