# Bot do Discord do NOC: recebe o webhook do Zabbix e publica no canal
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py teste.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 8081
CMD ["python", "bot.py"]
