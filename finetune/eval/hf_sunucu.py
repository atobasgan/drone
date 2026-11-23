"""llama-server yerine: egitilmis LoRA adaptorunu transformers ile acan kucuk HTTP sunucu.

    python3 -m finetune.eval.hf_sunucu --ad drone-0.6b-faz5 --port 8080 &
    python3 -m finetune.eval.olc_harita --etiket drone-0.6b-faz5 --kisa-prompt

GGUF / llama.cpp kurulu olmayan makinede olcum icin. Yalniz olc.py ve olc_harita.py'nin
kullandigi kismi (/health, /v1/chat/completions, greedy) taklit eder. FARK: llama-server
cevabi JSON semasiyla KISITLAR (grammar), bu sunucu kisitlamaz; sonuclar bu yuzden biraz
kotumser cikar. float32 calisir (Q8_0/Q4_K_M ile ayni degil, nicemleme kaybi yok).
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading

import torch

from ..ortak import MODELLER
from ..train.veri import prompt_metni


class Model:
    def __init__(self, yol, thread=0):
        from peft import AutoPeftModelForCausalLM
        from transformers import AutoTokenizer
        if thread:
            torch.set_num_threads(thread)
        self.tokenizer = AutoTokenizer.from_pretrained(yol)
        self.model = AutoPeftModelForCausalLM.from_pretrained(yol, dtype=torch.float32).merge_and_unload().eval()
        self.kilit = threading.Lock()

    @torch.no_grad()
    def cevapla(self, mesajlar, max_tokens):
        girdi = self.tokenizer(prompt_metni(self.tokenizer, mesajlar), return_tensors='pt', add_special_tokens=False)
        with self.kilit:
            cikti = self.model.generate(**girdi, max_new_tokens=max_tokens, do_sample=False)
        return self.tokenizer.decode(cikti[0][girdi['input_ids'].shape[1]:], skip_special_tokens=True).strip()


def isleyici(model):
    class Isleyici(BaseHTTPRequestHandler):
        def _yaz(self, kod, veri):
            govde = json.dumps(veri, ensure_ascii=False).encode()
            self.send_response(kod)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)

        def do_GET(self):
            self._yaz(200 if self.path == '/health' else 404, {'status': 'ok'})

        def do_POST(self):
            if self.path != '/v1/chat/completions':
                return self._yaz(404, {})
            istek = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            metin = model.cevapla(istek['messages'], int(istek.get('max_tokens', 128)))
            self._yaz(200, {'choices': [{'message': {'role': 'assistant', 'content': metin}}]})

        def log_message(self, *args):
            pass
    return Isleyici


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ad', default='drone-0.6b-faz5', help='finetune/models/<ad>/lora')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--thread', type=int, default=0)
    args = ap.parse_args(argv)
    model = Model(os.path.join(MODELLER, args.ad, 'lora'), args.thread)
    print(f'hazır: http://127.0.0.1:{args.port} ({args.ad})', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), isleyici(model)).serve_forever()


if __name__ == '__main__':
    main()
