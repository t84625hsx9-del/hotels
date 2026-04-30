FROM cr.yandex/mirror/python:3.11-slim

# 1. Добавляем libpq-dev для работы с Postgres
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Копируем код
COPY . .

# Открываем порты для Django (8000) и FastAPI (8001)
EXPOSE 8000
EXPOSE 8001


