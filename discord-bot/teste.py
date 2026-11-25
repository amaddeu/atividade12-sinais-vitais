#!/usr/bin/env python3
"""Manda um alerta Disaster de teste e, depois de alguns segundos, a recuperação dele.
Roda dentro do container: docker exec discord-bot python teste.py  (ou ./lab.sh discord-teste)"""
import json, os, sys, time, urllib.error, urllib.request

def enviar(dados):
    req = urllib.request.Request(f"http://localhost:{os.environ.get('BOT_PORT', '8081')}/zabbix",
                                 json.dumps(dados).encode(),
                                 {"Content-Type": "application/json", "X-Bot-Secret": os.environ.get("BOT_SECRET", "")})
    try:
        print(urllib.request.urlopen(req, timeout=20).read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"ERRO {e.code}: {e.read().decode()}")

agora = time.strftime("%Y.%m.%d"), time.strftime("%H:%M:%S")
base = {"event_id": f"teste-{int(time.time())}", "name": "TESTE - CPU do roteador de borda acima de 90% (média de 5 min)",
        "host": "Roteador de Borda - AS65010", "ip": "172.30.10.254", "severity": "Disaster", "nseverity": "5",
        "value": "97.50 %", "date": agora[0], "time": agora[1]}
print("Enviando PROBLEMA de teste..."); enviar({**base, "event_value": "1", "event_update": "0"})
time.sleep(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
print("Enviando RESOLUÇÃO de teste...")
enviar({**base, "event_value": "0", "event_update": "0", "value": "12.30 %", "duration": "10s",
        "recovery_date": time.strftime("%Y.%m.%d"), "recovery_time": time.strftime("%H:%M:%S")})
