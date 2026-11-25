#!/bin/bash
# Sobe o FRR (roteamento) e, se houver usuário SNMP definido, o agente snmpd com SNMPv3.
set -e

cp /config/frr.conf /etc/frr/frr.conf
chown frr:frr /etc/frr/frr.conf
/usr/lib/frr/frrinit.sh start

if [ -n "$SNMP_USER" ]; then
  # Gera o snmpd.conf: config base + usuário SNMPv3 (SHA-256 para autenticação, AES-128 para criptografia)
  cp /config/snmpd.conf /etc/snmp/snmpd.conf
  echo "createUser $SNMP_USER SHA-256 \"$SNMP_AUTH_PASS\" AES \"$SNMP_PRIV_PASS\"" >> /etc/snmp/snmpd.conf
  echo "rouser $SNMP_USER priv" >> /etc/snmp/snmpd.conf
  echo "[entrypoint] snmpd iniciando com SNMPv3 (usuario $SNMP_USER, nivel authPriv)"
  exec /usr/sbin/snmpd -f -Lo -u root -g root -p /run/snmpd.pid
else
  echo "[entrypoint] sem SNMP neste equipamento; FRR rodando"
  exec sleep infinity
fi
