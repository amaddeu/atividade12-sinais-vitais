#!/usr/bin/env python3
"""Troca só os endereços de e-mail (remetente do media type e destino do usuário noc), sem recriar nada.
Uso: python3 configurar_email.py --gmail remetente@gmail.com --noc destino@..."""
import argparse, json, os, urllib.request

API = os.environ.get("ZABBIX_API", "http://localhost:8080/api_jsonrpc.php")
tok = None
def call(m, p):
    req = urllib.request.Request(API, json.dumps({"jsonrpc": "2.0", "method": m, "params": p, "id": 1}).encode(),
                                 {"Content-Type": "application/json-rpc"})
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    r = json.load(urllib.request.urlopen(req, timeout=20))
    if "error" in r:
        raise RuntimeError(f"{m}: {r['error']}")
    return r["result"]

ap = argparse.ArgumentParser(); ap.add_argument("--gmail", required=True); ap.add_argument("--noc", required=True)
a = ap.parse_args()
tok = call("user.login", {"username": "Admin", "password": "zabbix"})
mt = call("mediatype.get", {"filter": {"name": "Gmail - NOC"}, "output": ["mediatypeid"]})[0]["mediatypeid"]
call("mediatype.update", {"mediatypeid": mt, "smtp_email": a.gmail, "username": a.gmail, "status": 0})
u = call("user.get", {"filter": {"username": "noc"}, "output": ["userid"]})[0]["userid"]
call("user.update", {"userid": u, "medias": [{"mediatypeid": mt, "sendto": [a.noc], "active": 0,
                                              "severity": 63, "period": "1-7,00:00-24:00"}]})
print(f"OK: remetente {a.gmail} | NOC recebe em {a.noc}")
