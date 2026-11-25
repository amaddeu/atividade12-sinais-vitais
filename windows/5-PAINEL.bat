@echo off
chcp 65001 >nul
title PAINEL - Atividade 12 (Ctrl+C para sair)
cd /d "%~dp0.."
:loop
cls
echo =====  LAB ATIVIDADE 12 - SINAIS VITAIS  ^|  %TIME%  ^|  Ctrl+C para sair  =====
docker compose run --rm --no-deps configurador python scripts/status.py
timeout /t 15 /nobreak >nul
goto loop
