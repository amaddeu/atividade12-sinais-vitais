@echo off
chcp 65001 >nul
title TESTES - BGP e SNMPv3
docker exec roteador-borda bash /scripts/testes.sh
pause
