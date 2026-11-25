@echo off
chcp 65001 >nul
title Configurar bot do Discord do NOC
cd /d "%~dp0.."
echo Bot do Discord do NOC (opcional). Precisa do TOKEN do bot e do ID do canal.
echo Passo a passo no README (secao "Bot do Discord").
echo.
set /p T=Token do bot: 
set /p C=ID do canal do NOC: 
set "R="
set /p R=ID do cargo a marcar no Disaster (Enter = nenhum): 
> discord.env echo DISCORD_TOKEN=%T%
>> discord.env echo DISCORD_CHANNEL_ID=%C%
>> discord.env echo DISCORD_ROLE_ID=%R%
echo discord.env gravado (fica so no seu PC). Reiniciando o bot...
docker compose up -d --build --force-recreate discord-bot
timeout /t 15 /nobreak >nul
docker exec discord-bot python -c "import urllib.request;print(urllib.request.urlopen('http://localhost:8081/saude').read().decode())"
echo.
echo Se apareceu "conectado": true, rode 9-DISCORD-TESTE.bat
echo Se nao, veja o erro com: docker logs discord-bot
pause
