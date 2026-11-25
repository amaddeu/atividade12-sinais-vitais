@echo off
cd /d "%~dp0.."
docker compose stop
echo Lab desligado (configuracao preservada). Para ligar de novo: 1-INICIAR.bat
pause
