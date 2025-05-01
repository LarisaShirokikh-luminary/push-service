FROM python:3.9-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry==1.5.1

# Отключаем виртуальное окружение — установка будет в system site-packages
RUN poetry config virtualenvs.create false

# Установка зависимостей (можно заменить на poetry install, если есть pyproject.toml)
RUN pip install --no-cache-dir "kafka-python>=2.0.2" "firebase-admin>=6.2.0"

COPY . .

EXPOSE 8080

CMD ["python", "push_test_app/server.py"]