#!/bin/bash
# Usado pelo snmpd (extend): devolve quantos prefixos o roteador recebeu via BGP.
vtysh -c 'show bgp ipv4 unicast summary json' 2>/dev/null \
  | jq '[.peers[]?.pfxRcd // 0] | add // 0'
