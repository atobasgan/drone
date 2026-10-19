# command_parser -> mission_executor. Tek ya da cok adimli komut listesi.

builtin_interfaces/Time t_konusma_bitti   # VAD konusma bitti (Faz 3; yoksa 0)
builtin_interfaces/Time t_metin_geldi     # parser metni aldi
builtin_interfaces/Time t_komut_hazir     # JSON komut hazir

DroneCommand[] adimlar
bool kuyruga_ekle    # false: mevcut kuyrugu iptal et, true: sona ekle

string metin         # komutun uretildigi (normalize) metin, log icin
string kaynak        # acil | hizli_yol | llm | terminal
