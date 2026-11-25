@echo off
chcp 65001 >nul
docker exec roteador-borda pkill stress-ng
docker exec isp-transito bash /scripts/rotas.sh retirar
timeout /t 3 /nobreak >nul
for /f %%p in ('docker exec roteador-borda bgp-rotas') do echo Rotas extras retiradas. Prefixos agora: %%p
pause
