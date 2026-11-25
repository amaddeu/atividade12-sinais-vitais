#!/usr/bin/env python3
"""Mostra o estado do lab pela API do Zabbix: últimos valores, problemas ativos e e-mails enviados."""
import json, os, time, urllib.request

API = os.environ.get("ZABBIX_API", "http://localhost:8080/api_jsonrpc.php")
_id = 0
token = None

def call(method, params):
    global _id
    _id += 1
    req = urllib.request.Request(API, json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": _id}).encode(),
                                 {"Content-Type": "application/json-rpc"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    r = json.load(urllib.request.urlopen(req, timeout=20))
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]

token = call("user.login", {"username": "Admin", "password": "zabbix"})
SEV = {"0": "N/C", "1": "Info", "2": "Warning", "3": "Average", "4": "High", "5": "DISASTER"}

h = call("host.get", {"filter": {"host": "Roteador-Borda"}, "output": ["hostid"],
                      "selectInterfaces": ["available", "error"]})[0]
iface = h["interfaces"][0]
print(f"Interface SNMP: {'DISPONIVEL' if iface['available'] == '1' else 'INDISPONIVEL/desconhecida'} {iface['error']}")

print("\n--- Itens (ultimo valor) ---")
for it in call("item.get", {"hostids": h["hostid"], "output": ["name", "key_", "lastvalue", "units", "lastclock", "state", "error"],
                            "sortfield": "name"}):
    if it["key_"] == "cpu.walk":
        val = f"{len(it['lastvalue'].splitlines())} linhas (nucleos)"
    else:
        val = f"{it['lastvalue']} {it['units']}"
    quando = time.strftime("%H:%M:%S", time.localtime(int(it["lastclock"]))) if it["lastclock"] != "0" else "nunca"
    erro = f"  ERRO: {it['error']}" if it["state"] == "1" else ""
    print(f"  {it['name']:<42} {val:<28} ({quando}){erro}")

print("\n--- Problemas ativos ---")
probs = call("problem.get", {"hostids": h["hostid"], "output": ["name", "severity", "clock"], "sortfield": "eventid", "sortorder": "DESC"})
for p in probs:
    print(f"  [{SEV[p['severity']]}] {p['name']} desde {time.strftime('%H:%M:%S', time.localtime(int(p['clock'])))}")
if not probs:
    print("  nenhum")

print("\n--- Ultimos e-mails (alertas) ---")
STATUS = {"0": "na fila", "1": "ENVIADO", "2": "FALHOU", "3": "novo"}
alerts = call("alert.get", {"output": ["clock", "sendto", "subject", "status", "error"], "sortfield": "alertid",
                            "sortorder": "DESC", "limit": 6})
for a in alerts:
    print(f"  {time.strftime('%H:%M:%S', time.localtime(int(a['clock'])))} {STATUS.get(a['status'], a['status'])} -> {a['sendto']}: {a['subject']}"
          + (f"\n      erro: {a['error']}" if a["error"] else ""))
if not alerts:
    print("  nenhum ainda")
