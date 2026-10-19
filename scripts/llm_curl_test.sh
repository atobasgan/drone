#!/usr/bin/env bash
# Gorev 2.3 kontrolu: /v1/chat/completions'a basit bir istek.
# Cevaptaki "timings" alaninda token/saniye (predicted_per_second) gorunur; not et.
set -euo pipefail
URL="${URL:-http://127.0.0.1:8080}"
METIN="${1:-500 m yüksel}"
curl -s "$URL/v1/chat/completions" -H 'Content-Type: application/json' -d @- <<JSON | python3 -m json.tool
{
  "messages": [
    {"role": "system", "content": "Drone komutunu JSON'a çevir. Örnek: {\"adimlar\":[{\"komut\":\"yuksel\",\"metre\":500}]} /no_think"},
    {"role": "user", "content": "$METIN"}
  ],
  "temperature": 0,
  "max_tokens": 64,
  "cache_prompt": true,
  "chat_template_kwargs": {"enable_thinking": false}
}
JSON
