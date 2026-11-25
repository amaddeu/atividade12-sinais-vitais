#!/usr/bin/env python3
"""Grava a senha de app do Gmail no media type 'Gmail - NOC' lendo do teclado/stdin (nunca de arquivo).
Uso: python3 configurar_senha.py   (e digite a senha; ela não aparece na tela)"""
import getpass, json, os, sys, urllib.request

def call(m, p, t=None):
    r = urllib.request.Request(os.environ.get("ZABBIX_API", "http://localhost:8080/api_jsonrpc.php"),
                               json.dumps({"jsonrpc": "2.0", "method": m, "params": p, "id": 1}).encode(),
                               {"Content-Type": "application/json-rpc"})
    if t:
        r.add_header("Authorization", "Bearer " + t)
    res = json.load(urllib.request.urlopen(r, timeout=20))
    if "error" in res:
        sys.exit(f"{m}: {res['error']}")
    return res["result"]

senha = (getpass.getpass("Senha de app do Gmail: ") if sys.stdin.isatty() else sys.stdin.readline()).replace(" ", "").strip()
if len(senha) != 16:
    sys.exit(f"senha de app deve ter 16 caracteres (veio {len(senha)})")
t = call("user.login", {"username": "Admin", "password": "zabbix"})
mt = call("mediatype.get", {"filter": {"name": "Gmail - NOC"}, "output": ["mediatypeid"]}, t)[0]["mediatypeid"]
call("mediatype.update", {"mediatypeid": mt, "passwd": senha, "status": 0}, t)
print("OK: senha gravada no Zabbix (media type 'Gmail - NOC' ativo)")
