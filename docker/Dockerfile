FROM python:3.9-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry==1.5.1

# Настройка Poetry
RUN poetry config virtualenvs.create false

# Установка базовых зависимостей
RUN pip install "kafka-python>=2.0.2" "firebase-admin>=6.2.0"

# Создание директорий
RUN mkdir -p /app/credentials

# Копируем entrypoint скрипт
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Копирование проекта произойдет при сборке в docker-compose

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "push_cli.py", "--all"]