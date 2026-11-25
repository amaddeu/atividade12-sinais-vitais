# Atividade 12 – "Sinais Vitais" no Setor Financeiro (Triggers Críticas)

**Grupo:** Amadeu Pinheiro (RA 206843) · Eder Maciel (RA 205969) · Renato Peixoto (RA 205683)

Lab 100% gratuito em Docker: um roteador de borda Linux com FRRouting (BGP) monitorado por
**SNMPv3 (authPriv)** a partir de um **Zabbix 7.0 LTS**. Quando a **média de CPU de 5 minutos passa de 90%**,
o Zabbix abre um problema **Disaster** e manda **e-mail ao NOC**.

Tudo sobe com um comando e se configura sozinho: não precisa instalar Zabbix, Ubuntu nem WSL na mão.

---

## Como executar (escolha UM jeito)

### Opção A – GitHub Codespaces (recomendado: roda no navegador, sem instalar nada)

1. Clique aqui: [![Abrir no GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/amaddeu/atividade12-sinais-vitais?quickstart=1)
   (ou, nesta página, **Code ▸ Codespaces ▸ Create codespace on main**).
2. Espere abrir o VS Code no navegador. O lab sobe sozinho no terminal (1ª vez: **3 a 6 minutos**).
   Quando aparecer `LAB PRONTO`, está tudo configurado.
3. Abra a aba **PORTS**, na porta **8080** clique no ícone do globo → abre o Zabbix.
   Login: **Admin** / **zabbix**.
4. No terminal do Codespace:

```bash
./lab.sh testes      # sessão BGP + 4 testes de segurança do SNMPv3
./lab.sh demo        # +10.000 rotas e CPU do roteador a 100% por 8 min
./lab.sh painel      # acompanha CPU, problemas e e-mails a cada 15 s (Ctrl+C sai)
```

> Se o terminal não mostrar o `LAB PRONTO`, rode `./lab.sh iniciar` (pode rodar quantas vezes quiser).
> Conta pessoal do GitHub tem horas grátis de Codespaces por mês; ao terminar, pare o codespace em
> https://github.com/codespaces.

### Opção B – Windows com Docker Desktop

1. Instale e abra o [Docker Desktop](https://www.docker.com/products/docker-desktop/) (espere ficar *running*).
2. Baixe o repositório (**Code ▸ Download ZIP**) e extraia.
3. Na pasta `windows\`, dê dois cliques:

| Arquivo | O que faz |
|---|---|
| `1-INICIAR.bat` | sobe os 6 containers, configura o Zabbix e abre http://localhost:8080 |
| `2-TESTES.bat` | sessão BGP + testes de segurança do SNMPv3 |
| `3-DEMO.bat` | ISP manda +10.000 rotas e a CPU do roteador vai a 100% por 8 min |
| `4-PARAR-DEMO.bat` | para o estresse e retira as rotas extras |
| `5-PAINEL.bat` | painel ao vivo (CPU, RAM, BGP, problemas, e-mails) |
| `6-EMAIL-OPCIONAL.bat` | liga o envio real de e-mail (Gmail + senha de app) |
| `7-DESLIGAR.bat` | para os containers (configuração preservada) |

### Opção C – Linux / macOS / WSL (qualquer máquina com Docker)

```bash
git clone https://github.com/amaddeu/atividade12-sinais-vitais.git && cd atividade12-sinais-vitais
./lab.sh iniciar     # depois: testes | demo | parar-demo | painel | status | email | desligar | apagar
```

Ou, sem os atalhos: `docker compose up -d --build` (o container `zbx-configurador` configura o Zabbix e termina).

---

## O que esperar na demo

| Tempo após `demo` | O que acontece |
|---|---|
| 0 min | BGP passa de 3.000 para 13.000 prefixos; CPU do roteador vai a 100% |
| ~4 min | média de 5 min > 70% e > 80% → **Warning** e **High** |
| ~5 min | média de 5 min > 90% → **DISASTER** + e-mail ao NOC (*Monitoring ▸ Problems*) |
| depois de `parar-demo` | média cai abaixo de 85% → problema **RESOLVIDO** + e-mail de recuperação |

**Sobre o e-mail:** sem configurar o Gmail, o Zabbix **dispara** o alerta mesmo assim, mas o envio aparece como
`FALHOU – Login denied` (não há senha). Isso prova que a action rodou (veja em *Reports ▸ Action log* ou no
`./lab.sh painel`). Para o e-mail chegar de verdade, rode `./lab.sh email` (ou `6-EMAIL-OPCIONAL.bat`) e informe
um Gmail com [senha de app](https://myaccount.google.com/apppasswords). A senha fica só no banco do Zabbix,
nunca em arquivo.

Logins: **Admin / zabbix** (administrador) · **noc / Operacao#2026** (operador NOC, só leitura).

---

## Topologia

```
 [isp-transito]  AS65020           [roteador-borda]  AS65010                    [zbx-server] Zabbix 7.0
 172.30.20.253  ---- eBGP ---->  172.30.20.254 | 172.30.10.254  <-- SNMPv3 UDP/161 --  172.30.10.20
  anuncia 3.000 prefixos          FRR (zebra+bgpd) + snmpd                              |
  (13.000 na demo)                 rede_wan          rede_gerencia          zbx-web :8080 + PostgreSQL 16
                                                                                       |
                                                                     smtp.gmail.com:587 STARTTLS --> NOC
```

| Container | Papel | Imagem |
|---|---|---|
| `roteador-borda` | Roteador L3 de borda do banco: BGP + agente SNMPv3 | Debian 12 + FRR 8.4 + net-snmp 5.9 (build local, `imagem-frr/`) |
| `isp-transito` | Provedor de trânsito (peer eBGP) que “enche” a tabela de rotas | mesma imagem, sem SNMP |
| `zbx-server` | Zabbix Server 7.0 (coleta SNMP, avalia triggers, envia e-mail) | `zabbix/zabbix-server-pgsql:alpine-7.0-latest` |
| `zbx-web` | Interface web (porta 8080) | `zabbix/zabbix-web-nginx-pgsql:alpine-7.0-latest` |
| `zbx-db` | Banco do Zabbix | `postgres:16-alpine` |
| `zbx-configurador` | Configura o Zabbix pela API e termina (`Exited (0)` = OK) | `python:3.12-slim` |

## Estrutura do repositório

```
docker-compose.yml        os 6 containers e as 2 redes
.env                      senhas do LAB (SNMPv3, banco) - fictícias, só existem nos containers
imagem-frr/               Dockerfile do roteador (FRR + snmpd + stress-ng) e entrypoint
roteador/                 frr.conf (BGP AS65010) e snmpd.conf (só SNMPv3) do roteador de borda
isp-transito/             frr.conf do provedor (AS65020, 3.000 prefixos)
scripts/configurar_zabbix.py   cria tudo no Zabbix via API (idempotente)
scripts/status.py         valores, problemas e e-mails pela API
scripts/testes.sh         testes de segurança SNMPv3 (roda dentro do roteador)
scripts/rotas.sh          anuncia/retira as 10.000 rotas da demo (roda dentro do ISP)
lab.sh                    atalhos Linux/macOS/Codespaces
windows/*.bat             atalhos Windows
.devcontainer/            configuração do GitHub Codespaces
```

## Passo a passo do que foi feito

### 1. Roteador de borda (FRR + SNMPv3)
- `roteador/frr.conf`: AS 65010, vizinho eBGP 172.30.20.253 (AS 65020), anuncia a rede interna 10.50.0.0/16.
- `roteador/snmpd.conf`: escuta só UDP/161, **sem `rocommunity`** (v1/v2c desligados).
- O `entrypoint.sh` acrescenta o usuário SNMPv3 vindo do `.env`:
  `createUser zbxmonitor SHA-256 "<auth>" AES "<priv>"` + `rouser zbxmonitor priv` (só aceita authPriv).
- `extend bgp_rotas` expõe por SNMP quantos prefixos o BGP recebeu.

**Testes de segurança (`./lab.sh testes`):**

| Teste | Resultado |
|---|---|
| SNMPv3 authPriv com senhas certas | responde (`sysName = roteador-borda`) |
| SNMPv3 com senha de autenticação errada | `Authentication failure` |
| SNMPv2c com comunidade `public` | `Timeout: No Response` (v2c não existe neste agente) |
| SNMPv3 sem autenticação (noAuthNoPriv) | `authorizationError (access denied)` |

### 2. BGP
- Sessão eBGP `Established` entre banco e ISP; o roteador recebe **3.000 prefixos** (`show bgp ipv4 unicast summary`).
- Na demo, o ISP passa a anunciar **13.000**.

### 3. OIDs usados (verificados com `snmpwalk` no próprio roteador)

| Métrica | OID | MIB |
|---|---|---|
| Carga de cada núcleo (% no último minuto) | `1.3.6.1.2.1.25.3.3.1.2` (walk, 1 linha por núcleo) | HOST-RESOURCES-MIB `hrProcessorLoad` |
| RAM total (KB) | `1.3.6.1.4.1.2021.4.5.0` | UCD-SNMP-MIB `memTotalReal` |
| RAM disponível (KB) | `1.3.6.1.4.1.2021.4.27.0` | UCD-SNMP-MIB `memSysAvail` |
| Prefixos BGP recebidos | `1.3.6.1.4.1.8072.1.3.2.3.1.1.9.98.103.112.95.114.111.116.97.115` | NET-SNMP-EXTEND-MIB |
| Nome / uptime | `1.3.6.1.2.1.1.5.0` / `1.3.6.1.2.1.1.3.0` | SNMPv2-MIB |

### 4. Zabbix (`scripts/configurar_zabbix.py`, via API, idempotente)
1. Grupo **Roteadores de Borda**.
2. Host **Roteador-Borda** (172.30.10.254:161), interface **SNMPv3, authPriv, SHA256, AES128**.
3. Itens:
   - `cpu.walk`: SNMP `walk[1.3.6.1.2.1.25.3.3.1.2]` a cada 30 s;
   - `cpu.util`: item dependente; pré-processamento JavaScript faz a **média dos núcleos**;
   - `mem.total` e `mem.available`: SNMP get, multiplicados por 1024 (KB → B);
   - `mem.util`: item calculado `100 * (1 - last(//mem.available) / last(//mem.total))`;
   - `bgp.prefixos`, `sys.name`, `sys.uptime`.
4. Triggers (matriz de severidade) para **CPU e RAM**:

   | Severidade | Expressão | Recupera quando |
   |---|---|---|
   | Disaster | `avg(/Roteador-Borda/cpu.util,5m)>90` | `avg(...,5m)<85` |
   | High | `avg(/Roteador-Borda/cpu.util,5m)>80` (depende do Disaster) | `<75` |
   | Warning | `avg(/Roteador-Borda/cpu.util,5m)>70` (depende do High) | `<65` |

   (idem para `mem.util`). A **dependência** impede que um nível mais baixo abra *depois* que o mais grave
   já está em problema. Numa subida gradual os níveis abrem em sequência: é a escalada.
   Extra: `nodata(/Roteador-Borda/cpu.util,3m)=1`, Disaster: “roteador sem resposta SNMP (possível congelamento)”.
5. Media type **Gmail - NOC**: `smtp.gmail.com:587`, STARTTLS, verificação de certificado, autenticação com **senha de app**.
6. Grupo de usuários **NOC - Operações** (leitura no grupo Roteadores de Borda) e usuário **noc**.
7. Action **NOC - Alerta crítico roteador de borda**: condição `grupo = Roteadores de Borda` **E** `severidade >= Disaster`
   → envia e-mail ao grupo NOC. Na recuperação, notifica todos os envolvidos (“[RESOLVIDO]”).

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `docker: command not found` / Docker não está rodando | abra o Docker Desktop (Windows/macOS) ou use o Codespaces |
| Porta 8080 já em uso | feche o outro programa ou troque `"8080:8080"` no `docker-compose.yml` |
| Zabbix abre mas o host aparece cinza | espere 1 a 2 min: a 1ª coleta SNMP leva até 1 minuto |
| Quero começar do zero | `./lab.sh apagar` e depois `./lab.sh iniciar` |
