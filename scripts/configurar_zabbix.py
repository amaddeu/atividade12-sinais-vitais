#!/usr/bin/env python3
"""
Atividade 12 - configura o Zabbix 7.0 via API (idempotente: pode rodar várias vezes).

Cria: grupo de hosts, host "Roteador-Borda" com interface SNMPv3 authPriv, itens de CPU/RAM/BGP,
triggers Warning/High/Disaster (CPU e RAM) + trigger de "sem resposta", media type de e-mail (Gmail),
grupo/usuário NOC e a action que manda e-mail ao NOC.

A senha de app do Gmail NÃO passa por aqui: ela é digitada na interface web
(Alertas > Tipos de mídia > Gmail - NOC), então nunca fica gravada em arquivo.

Roda sozinho no container "zbx-configurador" quando o lab sobe (docker compose up).
Manual:  python3 scripts/configurar_zabbix.py [--gmail conta@gmail.com --noc destino@gmail.com]
"""
import argparse, json, os, sys, time, urllib.request

API = os.environ.get("ZABBIX_API", "http://localhost:8080/api_jsonrpc.php")
HOST = "Roteador-Borda"
ROTEADOR_IP = "172.30.10.254"

def ler_env():
    env = {}
    if os.environ.get("SNMP_USER"):   # no container, as variáveis já vêm do .env pelo docker compose
        return {k: os.environ[k] for k in ("SNMP_USER", "SNMP_AUTH_PASS", "SNMP_PRIV_PASS")}
    caminho = os.path.join(os.path.dirname(__file__), "..", ".env")
    for linha in open(caminho, encoding="utf-8"):
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            env[k] = v
    return env

class Zabbix:
    def __init__(self):
        self.token = None
        self.n = 0

    def call(self, method, params):
        self.n += 1
        body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": self.n}).encode()
        req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json-rpc"})
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        resp = json.load(urllib.request.urlopen(req, timeout=30))
        if "error" in resp:
            raise RuntimeError(f"{method}: {resp['error']['message']} {resp['error']['data']}")
        return resp["result"]

    def login(self):
        for _ in range(90):   # 1a subida: o Zabbix cria o banco, pode levar uns minutos
            try:
                self.token = self.call("user.login", {"username": "Admin", "password": "zabbix"})
                return
            except Exception as e:
                print("  aguardando a API do Zabbix subir...", type(e).__name__, flush=True)
                time.sleep(5)
        sys.exit("API do Zabbix não respondeu")

def apagar_se_existir(z, obj, campo, nome, idcampo):
    achados = z.call(f"{obj}.get", {"filter": {campo: nome}, "output": [idcampo]})
    if achados:
        z.call(f"{obj}.delete", [a[idcampo] for a in achados])

JS_MEDIA_CPU = r"""
// O walk devolve uma linha por núcleo:  .1.3.6.1.2.1.25.3.3.1.2.196608 = INTEGER: 37
// hrProcessorLoad = % de uso de cada núcleo no último minuto. Aqui tiramos a média de todos.
var soma = 0, n = 0;
value.split('\n').forEach(function (linha) {
    var m = linha.match(/=\s*INTEGER:\s*(\d+)/);
    if (m) { soma += parseInt(m[1], 10); n++; }
});
if (n === 0) { throw 'walk sem valores de hrProcessorLoad'; }
return (soma / n).toFixed(2);
"""

# Passo 1: regex "INTEGER:" descarta o walk vazio do 1o minuto do agente (sem erro); passo 2: média em JS
PREPROC_CPU = [
    {"type": 14, "params": "INTEGER:", "error_handler": 1, "error_handler_params": ""},
    {"type": 21, "params": JS_MEDIA_CPU, "error_handler": 0, "error_handler_params": ""},
]

MSG_PROBLEMA = """ALERTA NOC - Roteador de borda (Atividade 12 - Sinais Vitais)

Problema: {EVENT.NAME}
Severidade: {EVENT.SEVERITY}
Equipamento: {HOST.NAME} ({HOST.IP})
Valor atual: {ITEM.LASTVALUE1}
Início: {EVENT.DATE} {EVENT.TIME}
ID do evento: {EVENT.ID}

Ação sugerida: verificar sessões BGP, filtrar/limitar prefixos (maximum-prefix) e conferir processos no roteador."""

MSG_RECUPERACAO = """RESOLVIDO - Roteador de borda

Problema: {EVENT.NAME}
Equipamento: {HOST.NAME} ({HOST.IP})
Resolvido em: {EVENT.RECOVERY.DATE} {EVENT.RECOVERY.TIME}
Duração do problema: {EVENT.DURATION}
Valor atual: {ITEM.LASTVALUE1}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gmail", default=os.environ.get("GMAIL_REMETENTE") or "remetente@gmail.com",
                    help="conta Gmail que ENVIA (remetente) - trocável depois com ./lab.sh email")
    ap.add_argument("--noc", default=os.environ.get("EMAIL_NOC") or "noc@exemplo.com",
                    help="e-mail do NOC que RECEBE o alerta")
    ap.add_argument("--se-nao-existir", action="store_true",
                    help="não mexe em nada se o host Roteador-Borda já existir (preserva o histórico)")
    a = ap.parse_args()
    env = ler_env()
    z = Zabbix()
    print("1) Login na API"); z.login()
    # Interface em inglês britânico = horário em 24h (o padrão en_US mostra 08:02 PM)
    for u in z.call("user.get", {"filter": {"username": "Admin"}, "output": ["userid"]}):
        z.call("user.update", {"userid": u["userid"], "lang": "en_GB"})
    # Remove o host padrão "Zabbix server" (não há agente no container; aparecia em vermelho e confundia)
    padrao = z.call("host.get", {"filter": {"host": "Zabbix server"}, "output": ["hostid"]})
    if padrao:
        z.call("host.delete", [h["hostid"] for h in padrao])
    if a.se_nao_existir and z.call("host.get", {"filter": {"host": HOST}, "output": ["hostid"]}):
        print("Zabbix ja configurado (host Roteador-Borda existe) - mantendo como esta.")
        print("OK - Zabbix configurado.")
        return

    # Remove a action padrão desativada do Zabbix (aparecia em vermelho na lista)
    apagar_se_existir(z, "action", "name", "Report problems to Zabbix administrators", "actionid")

    # Limpa o que este script criou antes (idempotência; nomes antigos sem acento também)
    apagar_se_existir(z, "action", "name", "NOC - Alerta critico roteador de borda", "actionid")
    apagar_se_existir(z, "usergroup", "name", "NOC - Operacoes", "usrgrpid")
    apagar_se_existir(z, "action", "name", "NOC - Alerta crítico roteador de borda", "actionid")
    apagar_se_existir(z, "user", "username", "noc", "userid")
    apagar_se_existir(z, "host", "host", HOST, "hostid")
    apagar_se_existir(z, "mediatype", "name", "Gmail - NOC", "mediatypeid")
    apagar_se_existir(z, "usergroup", "name", "NOC - Operações", "usrgrpid")

    print("2) Grupo de hosts")
    g = z.call("hostgroup.get", {"filter": {"name": "Roteadores de Borda"}, "output": ["groupid"]})
    groupid = g[0]["groupid"] if g else z.call("hostgroup.create", {"name": "Roteadores de Borda"})["groupids"][0]

    print("3) Host com interface SNMPv3 authPriv (SHA-256 + AES-128)")
    hostid = z.call("host.create", {
        "host": HOST,
        "name": "Roteador de Borda - AS65010",
        "description": "Roteador L3 de borda do banco (FRRouting/BGP). Monitorado por SNMPv3 authPriv.",
        "groups": [{"groupid": groupid}],
        "interfaces": [{
            "type": 2, "main": 1, "useip": 1, "ip": ROTEADOR_IP, "dns": "", "port": "161",
            "details": {
                "version": 3, "bulk": 1,
                "securityname": env["SNMP_USER"],
                "securitylevel": 2,                 # authPriv
                "authprotocol": 3,                  # SHA256
                "authpassphrase": env["SNMP_AUTH_PASS"],
                "privprotocol": 1,                  # AES128
                "privpassphrase": env["SNMP_PRIV_PASS"],
                "contextname": "",
            },
        }],
    })["hostids"][0]
    interfaceid = z.call("hostinterface.get", {"hostids": hostid, "output": ["interfaceid"]})[0]["interfaceid"]

    print("4) Itens")
    def item(**kw):
        base = {"hostid": hostid}
        if kw.get("type") == 20:
            base["interfaceid"] = interfaceid
        base.update(kw)
        return z.call("item.create", base)["itemids"][0]

    # CPU: walk em hrProcessorLoad (um valor por núcleo) -> item dependente com a média
    cpu_walk = item(name="CPU - Carga de cada núcleo (walk SNMP)", key_="cpu.walk", type=20,
                    snmp_oid="walk[1.3.6.1.2.1.25.3.3.1.2]", value_type=4, delay="30s",
                    history="1d", trends="0")
    item(name="CPU - Utilização média", key_="cpu.util", type=18, master_itemid=cpu_walk,
         value_type=0, units="%", history="7d",
         preprocessing=PREPROC_CPU)

    # RAM: total e disponível (UCD-SNMP-MIB, em KB -> multiplica por 1024) + item calculado em %
    item(name="RAM - Total", key_="mem.total", type=20, snmp_oid="get[1.3.6.1.4.1.2021.4.5.0]",
         value_type=3, units="B", delay="1m",
         preprocessing=[{"type": 1, "params": "1024", "error_handler": 0, "error_handler_params": ""}])
    item(name="RAM - Disponível", key_="mem.available", type=20, snmp_oid="get[1.3.6.1.4.1.2021.4.27.0]",
         value_type=3, units="B", delay="30s",
         preprocessing=[{"type": 1, "params": "1024", "error_handler": 0, "error_handler_params": ""}])
    item(name="RAM - Utilização", key_="mem.util", type=15, value_type=0, units="%", delay="30s",
         params=f"100 * (1 - last(//mem.available) / last(//mem.total))")

    # Contexto: rotas BGP recebidas (extend do snmpd) e uptime
    item(name="BGP - Prefixos recebidos do ISP", key_="bgp.prefixos", type=20,
         snmp_oid="get[1.3.6.1.4.1.8072.1.3.2.3.1.1.9.98.103.112.95.114.111.116.97.115]",
         value_type=3, delay="30s")
    item(name="Sistema - Nome (sysName)", key_="sys.name", type=20, snmp_oid="get[1.3.6.1.2.1.1.5.0]",
         value_type=1, delay="1h", history="7d", trends="0")
    item(name="Sistema - Uptime do agente SNMP", key_="sys.uptime", type=20, snmp_oid="get[1.3.6.1.2.1.1.3.0]",
         value_type=3, units="uptime", delay="1m",
         preprocessing=[{"type": 1, "params": "0.01", "error_handler": 0, "error_handler_params": ""}])

    print("5) Triggers (matriz de severidade Warning/High/Disaster com dependencias)")
    def matriz(chave, recurso):
        ids = {}
        # (limite, severidade, rótulo) - severidade Zabbix: 2=Warning, 4=High, 5=Disaster
        for limite, sev, rot in [(90, 5, "DISASTER"), (80, 4, "HIGH"), (70, 2, "WARNING")]:
            t = {
                "description": f"{recurso} do roteador de borda acima de {limite}% (média de 5 min)",
                "expression": f"avg(/{HOST}/{chave},5m)>{limite}",
                "recovery_mode": 1,
                "recovery_expression": f"avg(/{HOST}/{chave},5m)<{limite - 5}",
                "priority": sev,
                "manual_close": 1,
                "comments": f"Nível {rot}. Dispara quando a MÉDIA dos últimos 5 minutos passa de {limite}%. "
                            f"Só volta ao normal abaixo de {limite - 5}% (histerese, evita alerta pisca-pisca).",
            }
            # Warning depende de High E Disaster; High depende de Disaster
            superiores = {5: [], 4: [ids.get(5)], 2: [ids.get(4), ids.get(5)]}[sev]
            if superiores:
                t["dependencies"] = [{"triggerid": s} for s in superiores]
            ids[sev] = z.call("trigger.create", t)["triggerids"][0]
    matriz("cpu.util", "CPU")
    matriz("mem.util", "RAM")
    z.call("trigger.create", {
        "description": "Roteador de borda sem resposta SNMP há 3 min (possível congelamento)",
        "expression": f"nodata(/{HOST}/cpu.util,3m)=1",
        "priority": 5,
        "comments": "Se o roteador congelar de vez, ele para de responder e a média de CPU não chega. Esta trigger cobre esse caso.",
    })

    print("6) Media type de e-mail (Gmail SMTP 587 STARTTLS) - senha gravada no passo seguinte")
    mediatypeid = z.call("mediatype.create", {
        "type": 0, "name": "Gmail - NOC", "provider": 0, "status": 0,   # 0 = ativo (a API cria DESATIVADO por padrao)
        "smtp_server": "smtp.gmail.com", "smtp_port": 587, "smtp_helo": "gmail.com",
        "smtp_email": a.gmail, "smtp_security": 1, "smtp_verify_peer": 1, "smtp_verify_host": 1,
        "smtp_authentication": 1, "username": a.gmail, "passwd": "",
        "message_format": 0,
        "message_templates": [
            {"eventsource": 0, "recovery": 0, "subject": "[{EVENT.SEVERITY}] {EVENT.NAME}", "message": MSG_PROBLEMA},
            {"eventsource": 0, "recovery": 1, "subject": "[RESOLVIDO] {EVENT.NAME}", "message": MSG_RECUPERACAO},
        ],
    })["mediatypeids"][0]

    print("7) Grupo e usuario NOC")
    usrgrpid = z.call("usergroup.create", {
        "name": "NOC - Operações",
        "hostgroup_rights": [{"id": groupid, "permission": 2}],   # 2 = leitura
    })["usrgrpids"][0]
    z.call("user.create", {
        "username": "noc", "name": "NOC", "surname": "Banco", "passwd": "Operacao#2026",
        "roleid": "1", "usrgrps": [{"usrgrpid": usrgrpid}],
        "medias": [{"mediatypeid": mediatypeid, "sendto": [a.noc], "active": 0,
                    "severity": 63, "period": "1-7,00:00-24:00"}],
    })

    print("8) Action: Disaster no grupo 'Roteadores de Borda' -> e-mail para o NOC")
    z.call("action.create", {
        "name": "NOC - Alerta crítico roteador de borda",
        "eventsource": 0, "status": 0, "esc_period": "1h",
        "filter": {"evaltype": 1, "conditions": [
            {"conditiontype": 0, "operator": 0, "value": groupid},     # grupo de hosts = Roteadores de Borda
            {"conditiontype": 4, "operator": 5, "value": "5"},          # severidade >= Disaster
        ]},
        "operations": [{"operationtype": 0, "esc_step_from": 1, "esc_step_to": 1,
                        "opmessage": {"default_msg": 1, "mediatypeid": mediatypeid},
                        "opmessage_grp": [{"usrgrpid": usrgrpid}]}],
        "recovery_operations": [{"operationtype": 11, "opmessage": {"default_msg": 1}}],
    })
    print("\nOK - Zabbix configurado.")
    print("E-mail real (opcional): ./lab.sh email  ou  windows/6-EMAIL-OPCIONAL.bat")

if __name__ == "__main__":
    main()
