FROM python:3.11-slim

RUN pip install --no-cache-dir python-telegram-bot==20.8 python-dotenv

WORKDIR /app
COPY . .

ENV TELEGRAM_BOT_TOKEN=""
EXPOSE 8080

CMD ["python", "__main__.py"]