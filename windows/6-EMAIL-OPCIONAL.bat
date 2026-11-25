@echo off
chcp 65001 >nul
title Configurar e-mail real do alerta
cd /d "%~dp0.."
echo Envio REAL do alerta por Gmail (opcional). Precisa de uma senha de app:
echo https://myaccount.google.com/apppasswords
echo.
set /p G=Gmail que ENVIA o alerta (remetente): 
set /p N=E-mail do NOC que RECEBE o alerta: 
docker compose run --rm --no-deps configurador python scripts/configurar_email.py --gmail "%G%" --noc "%N%"
echo Digite a senha de app (16 letras):
docker compose run --rm --no-deps -it configurador python scripts/configurar_senha.py
pause
