FROM python:3.9-slim

WORKDIR /app

# Установка Poetry
RUN pip install poetry==1.5.1

# Копируем проект полностью, включая код и конфиги
COPY . .

# Настройка Poetry
RUN poetry config virtualenvs.create false

# Установка зависимостей (обновлено на рекомендуемый синтаксис)
RUN pip install "kafka-python>=2.0.2" && \
    poetry install --only main

# Установка прав и определение entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "push_cli.py", "--all"]