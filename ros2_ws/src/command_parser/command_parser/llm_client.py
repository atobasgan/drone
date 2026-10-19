"""llama-server HTTP istemcisi (OpenAI uyumlu /v1/chat/completions).

Hiz icin (MIMARI.txt 3.7, 9.2):
  - temperature=0, max_tokens=64   -> deterministik, sinirli gecikme
  - response_format json_schema    -> cikti %100 semaya uygun JSON
  - cache_prompt=true              -> sistem prompt'u KV-cache'te kalir
  - dusunme modu kapali (/no_think + enable_thinking=false)
  - requests.Session               -> HTTP baglantisi acik tutulur (keep-alive)
"""
from dataclasses import dataclass
import json
import time

import requests

from .prompt import SISTEM_PROMPT
from .schema import KOMUT_SEMASI, SemaHatasi, dogrula


@dataclass
class LLMSonuc:
    adimlar: list = None     # dogrulanmis adim listesi (hata varsa None)
    ham: str = ''            # modelin ham cevabi
    sure_ms: float = 0.0
    hata: str = ''

    @property
    def basarili(self):
        return self.adimlar is not None


def _json_ayikla(metin):
    """Olasi <think></think> artigini ya da onekleri atlayip ilk JSON nesnesini alir."""
    bas = metin.find('{')
    son = metin.rfind('}')
    if bas < 0 or son < bas:
        raise ValueError('cevapta JSON yok')
    return json.loads(metin[bas:son + 1])


class LLMIstemcisi:

    def __init__(self, url='http://127.0.0.1:8080', model='yerel', zaman_asimi=5.0,
                 max_tokens=64, sistem_prompt=SISTEM_PROMPT, sema=KOMUT_SEMASI,
                 oturum=None):
        self.url = url.rstrip('/')
        self.model = model
        self.zaman_asimi = zaman_asimi
        self.max_tokens = max_tokens
        self.sistem_prompt = sistem_prompt
        self.sema = sema
        self.oturum = oturum or requests.Session()

    def istek_govdesi(self, metin):
        return {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self.sistem_prompt},
                {'role': 'user', 'content': metin},
            ],
            'temperature': 0,
            'max_tokens': self.max_tokens,
            'cache_prompt': True,
            'response_format': {
                'type': 'json_schema',
                'json_schema': {'name': 'drone_komut', 'strict': True, 'schema': self.sema},
            },
            'chat_template_kwargs': {'enable_thinking': False},
        }

    def cevir(self, metin):
        """Normalize metni komut adimlarina cevirir. Hicbir zaman istisna firlatmaz."""
        t0 = time.perf_counter()
        try:
            yanit = self.oturum.post(f'{self.url}/v1/chat/completions',
                                     json=self.istek_govdesi(metin), timeout=self.zaman_asimi)
            yanit.raise_for_status()
            ham = yanit.json()['choices'][0]['message'].get('content') or ''
        except (requests.RequestException, KeyError, IndexError, ValueError) as e:
            return LLMSonuc(sure_ms=(time.perf_counter() - t0) * 1000, hata=f'istek: {e}')
        sure = (time.perf_counter() - t0) * 1000
        try:
            adimlar = dogrula(_json_ayikla(ham))
        except (ValueError, SemaHatasi) as e:
            return LLMSonuc(ham=ham, sure_ms=sure, hata=f'gecersiz cevap: {e}')
        return LLMSonuc(adimlar=adimlar, ham=ham, sure_ms=sure)

    def saglikli(self):
        try:
            return self.oturum.get(f'{self.url}/health', timeout=2.0).status_code == 200
        except requests.RequestException:
            return False

    def isit(self):
        """Acilista bir istek: model ve sistem prompt'u bellege/KV-cache'e alinir."""
        return self.cevir('kalk')
