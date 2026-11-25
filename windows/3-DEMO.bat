@echo off
chcp 65001 >nul
title DEMO - Sobrecarga no roteador de borda
echo ISP anunciando +10.000 rotas para o roteador de borda...
docker exec isp-transito bash /scripts/rotas.sh anunciar
timeout /t 5 /nobreak >nul
for /f %%p in ('docker exec roteador-borda bgp-rotas') do echo    Prefixos recebidos agora: %%p
echo Estressando todos os nucleos do roteador a 100%% por 8 minutos (stress-ng)...
docker exec -d roteador-borda stress-ng --cpu 0 --cpu-load 100 --timeout 8m
echo.
echo Inicio: %TIME%. Em cerca de 6 minutos a media de 5 min passa de 90%%:
echo Warning - High - DISASTER no Zabbix (Monitoring ^> Problems) e e-mail ao NOC.
echo Acompanhe pelo 5-PAINEL.bat. Pode fechar esta janela.
pause
