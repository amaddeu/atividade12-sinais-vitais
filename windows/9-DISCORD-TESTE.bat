@echo off
chcp 65001 >nul
title Teste do bot do Discord
cd /d "%~dp0.."
echo Mandando um Disaster de teste e a resolucao dele para o canal do Discord...
docker exec discord-bot python teste.py 10
pause
