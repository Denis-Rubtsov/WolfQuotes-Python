# Базовый образ с Python
FROM python:3.11-slim

# Устанавливаем зависимости (без кеша)
RUN pip install --no-cache-dir python-telegram-bot==20.8 python-dotenv

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем весь проект внутрь контейнера
COPY . .

# Указываем переменную окружения для токена (можно переопределять при запуске)
ENV TELEGRAM_BOT_TOKEN=""

# Запускаем бота
CMD ["python", "__main__.py"]