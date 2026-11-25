@echo off
chcp 65001 >nul
title LAB ATIVIDADE 12 - Sinais Vitais
cd /d "%~dp0.."
echo ==============================================================
echo   Atividade 12 - Sinais Vitais no Setor Financeiro
echo   Precisa so do Docker Desktop aberto (nao precisa de Ubuntu)
echo ==============================================================
docker info >nul 2>&1
if errorlevel 1 goto semdocker
echo.
echo [1/3] Subindo os containers (1a vez baixa ~600 MB, 3 a 6 min)...
docker compose up -d --build
if errorlevel 1 goto erro
echo.
echo [2/3] Configurando o Zabbix pela API...
docker logs -f zbx-configurador
for /f %%c in ('docker wait zbx-configurador') do set "RC=%%c"
if not "%RC%"=="0" goto erro
echo.
echo [3/3] Aguardando o BGP...
timeout /t 20 /nobreak >nul
for /f %%p in ('docker exec roteador-borda bgp-rotas') do echo    Prefixos BGP recebidos do ISP: %%p
echo.
echo ======  LAB PRONTO: http://localhost:8080   (Admin / zabbix)  ======
start "" http://localhost:8080
echo Proximos: 2-TESTES.bat, 3-DEMO.bat, 5-PAINEL.bat
pause
goto :eof
:semdocker
echo.
echo [ERRO] O Docker nao esta rodando neste PC.
echo Instale/abra o Docker Desktop: https://www.docker.com/products/docker-desktop/
echo Espere o icone da baleia ficar "running" e rode este arquivo de novo.
echo Sem permissao para instalar? Use o GitHub Codespaces (ver README).
pause
goto :eof
:erro
echo.
echo [ERRO] Algo falhou acima. Rode este arquivo de novo; se repetir, veja o README.
pause
