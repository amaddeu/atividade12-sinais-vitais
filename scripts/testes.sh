#!/bin/bash
# Roda DENTRO do container roteador-borda (chamado pelo lab.sh testes / TESTES.bat).
# Mostra a sessão BGP e os 4 testes de segurança do SNMPv3. As senhas vêm do .env (variáveis do container).
R=172.30.10.254
OID=1.3.6.1.2.1.1.5.0   # sysName
titulo() { echo; echo "------------------------------------------------------------"; echo " $1"; echo "------------------------------------------------------------"; }
rodar() { "$@" 2>&1 | sed 's/^/   /'; }

echo "============  TESTES AO VIVO - ROTEADOR DE BORDA  ============"

titulo "1) BGP: o roteador (AS65010) conversa com o provedor (AS65020)?"
vtysh -c "show bgp ipv4 unicast summary" | grep -A1 Neighbor | sed 's/^/   /'
echo "   -> State/PfxRcd = quantas rotas o provedor mandou"

titulo "2) SNMPv3 authPriv com as senhas CERTAS (como o Zabbix faz)"
rodar snmpget -v3 -l authPriv -u "$SNMP_USER" -a SHA-256 -A "$SNMP_AUTH_PASS" -x AES -X "$SNMP_PRIV_PASS" $R $OID
echo "   -> RESPONDE: so quem tem as duas senhas le o roteador"

titulo "3) SNMPv3 com a senha de autenticacao ERRADA"
rodar snmpget -v3 -l authPriv -u "$SNMP_USER" -a SHA-256 -A "senhaErrada123" -x AES -X "$SNMP_PRIV_PASS" -r 0 $R $OID
echo "   -> BLOQUEADO"

titulo "4) SNMP v2c com a comunidade 'public' (o jeito antigo, sem criptografia)"
rodar snmpget -v2c -c public -t 2 -r 0 $R $OID
echo "   -> BLOQUEADO: v1/v2c estao desligados neste roteador"

titulo "5) SNMPv3 SEM autenticacao (noAuthNoPriv)"
rodar snmpget -v3 -l noAuthNoPriv -u "$SNMP_USER" -r 0 $R $OID
echo "   -> BLOQUEADO"
echo
