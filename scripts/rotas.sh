#!/bin/bash
# Roda DENTRO do container isp-transito (chamado pelo lab.sh / DEMO.bat).
#   bash /scripts/rotas.sh anunciar  -> ISP passa a anunciar +10.000 prefixos (3.000 -> 13.000)
#   bash /scripts/rotas.sh retirar   -> retira os 10.000 extras
NO=""; [ "$1" = "retirar" ] && NO="no "
{
  echo "router bgp 65020"; echo " address-family ipv4 unicast"
  for i in $(seq 3000 12999); do echo "  ${NO}network 100.$((64 + i / 256)).$((i % 256)).0/24"; done
  echo " exit-address-family"
} > /tmp/rotas.conf
vtysh -f /tmp/rotas.conf >/dev/null
