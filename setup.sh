#!/bin/bash
set -e

# Функция для вывода сообщений
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Создание необходимых директорий
mkdir -p logs
mkdir -p credentials
mkdir -p docker

# Проверка файлов проекта
if [ ! -f "pyproject.toml" ]; then
  log "ОШИБКА: Не найден файл pyproject.toml. Убедитесь, что скрипт запускается из корня проекта."
  exit 1
fi

# Создаем Dockerfile, если его нет
if [ ! -f "docker/Dockerfile" ]; then
  log "Создание Dockerfile..."
  cat > docker/Dockerfile << 'EOL'
FROM python:3.9-slim

# Установка рабочей директории
WORKDIR /app

# Установка Poetry
RUN pip install poetry==1.5.1

# Сначала копируем файлы проекта
COPY pyproject.toml poetry.lock* ./
COPY README.md ./
COPY push_service ./push_service
COPY tests ./tests
COPY examples ./examples

# Настройка Poetry для не использования виртуального окружения внутри контейнера
RUN poetry config virtualenvs.create false

# Установка зависимостей
RUN pip install "kafka-python>=2.0.2" && \
    poetry install --no-dev --no-interaction --no-ansi

# Копирование скрипта запуска
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Определение точки входа
ENTRYPOINT ["/entrypoint.sh"]

# Запуск по умолчанию
CMD ["python", "simple_test.py"]
EOL
  log "Dockerfile создан."
fi

# Создаем entrypoint.sh, если его нет
if [ ! -f "docker/entrypoint.sh" ]; then
  log "Создание entrypoint.sh..."
  cat > docker/entrypoint.sh << 'EOL'
#!/bin/bash
set -e

# Проверка наличия файла учетных данных Firebase
if [ ! -f "$FIREBASE_CREDENTIALS_PATH" ]; then
    echo "ОШИБКА: Файл учетных данных Firebase не найден по пути: $FIREBASE_CREDENTIALS_PATH"
    echo "Проверьте наличие файла: $(ls -la /app/)"
    
    # Создаем демо версию файла credentials для тестирования
    echo "Создаю демо версию файла учетных данных для тестирования..."
    cat > /app/serviceAccountKey.json << 'EOF'
{
  "type": "service_account",
  "project_id": "demo-project",
  "private_key_id": "demo-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIBVAIBADANBgkqhkiG9w0BAQEFAASCAT4wggE6AgEAAkEAq7BFUpkGp3+LQmlQ\nYx2eqzDV+xeG8kx/sQFV8qIw7Z5mvluEyPpJyRXLY4MFEFFJ8MbLCNYuCKTQZGSM\n+KPhXQIDAQAB\n-----END PRIVATE KEY-----",
  "client_email": "demo@demo-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/demo"
}
EOF
    echo "Создан демонстрационный файл учетных данных. Для реальной отправки уведомлений используйте настоящий файл."
fi

# Создание директории для логов, если её нет
mkdir -p /app/logs

# Запуск команды, переданной в аргументах
exec "$@"
EOL
  chmod +x docker/entrypoint.sh
  log "entrypoint.sh создан."
fi

# Создаем docker-compose.yml, если его нет
if [ ! -f "docker/docker-compose.yml" ]; then
  log "Создание docker-compose.yml..."
  cat > docker/docker-compose.yml << 'EOL'
version: '3.8'

services:
  push-service:
    build:
      context: ..
      dockerfile: ./docker/Dockerfile
    container_name: push-notification-service
    environment:
      - FIREBASE_CREDENTIALS_PATH=/app/serviceAccountKey.json
      - TEST_FCM_TOKEN=${TEST_FCM_TOKEN}
      - TEST_FCM_TOKEN_2=${TEST_FCM_TOKEN_2}
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_NOTIFICATION_TOPIC=notification_events
    volumes:
      - ../credentials/push-service-e154f-firebase-adminsdk-fbsvc-750b157407.json:/app/serviceAccountKey.json
      - ../logs:/app/logs
      - ../simple_test.py:/app/simple_test.py
    command: ["python", "simple_test.py"]
    depends_on:
      - kafka
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
EOL
  log "docker-compose.yml создан."
fi

# Создаем простой тестовый скрипт
if [ ! -f "simple_test.py" ]; then
  log "Создание simple_test.py..."
  cat > simple_test.py << 'EOL'
#!/usr/bin/env python
"""
Простая утилита для тестирования сервиса push-уведомлений.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_test")

def test_firebase():
    """
    Тестирование подключения к Firebase
    """
    try:
        # Импортируем здесь, чтобы уловить возможные ошибки импорта
        from push_service import FirebasePushService
        
        # Получаем путь к файлу учетных данных
        service_account_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
        
        # Проверяем наличие файла
        if not os.path.exists(service_account_path):
            logger.error(f"Файл учетных данных Firebase не найден: {service_account_path}")
            logger.info(f"Доступные файлы: {os.listdir('.')}")
            return False
        
        logger.info(f"Файл учетных данных Firebase найден: {service_account_path}")
        
        # Пытаемся инициализировать Firebase
        firebase = FirebasePushService.get_instance(service_account_path)
        logger.info("Firebase успешно инициализирован")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании Firebase: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_firebase_send():
    """
    Тестирование отправки сообщения Firebase
    """
    try:
        # Импортируем здесь, чтобы уловить возможные ошибки импорта
        from push_service import FirebasePushService
        
        # Получаем путь к файлу учетных данных
        service_account_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
        
        # Проверяем наличие токена FCM
        test_token = os.environ.get('TEST_FCM_TOKEN')
        if not test_token:
            logger.warning("Переменная TEST_FCM_TOKEN не установлена, используется тестовый токен")
            test_token = "test_token_for_testing"  # Это не будет работать, но позволит нам протестировать код
        
        # Пытаемся отправить сообщение
        firebase = FirebasePushService.get_instance(service_account_path)
        result = firebase.send_push(
            token=test_token,
            title="Test Title",
            body="This is a test message",
            data={"test": "value"}
        )
        
        logger.info(f"Сообщение отправлено: {result}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_notification_service():
    """
    Тестирование сервиса уведомлений
    """
    try:
        # Импортируем здесь, чтобы уловить возможные ошибки импорта
        from push_service import NotificationService
        from push_service.models import MockClient
        
        # Создаем мок базы данных
        class MockDB:
            def __init__(self, clients=None):
                self.clients = clients or {}
                self.client = self
            
            def get_by_core_id(self, core_id):
                return self.clients.get(core_id)
        
        # Создаем тестового клиента
        mock_clients = {
            "12345": MockClient(
                core_id="12345",
                firebase_token=os.environ.get("TEST_FCM_TOKEN", "test_token_for_testing"),
                language="en",
            )
        }
        
        # Создаем мок базы данных
        mock_db = MockDB(mock_clients)
        
        # Получаем путь к файлу учетных данных
        service_account_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
        
        # Создаем сервис уведомлений
        service = NotificationService(
            db=mock_db,
            service_account_path=service_account_path
        )
        
        logger.info("Сервис уведомлений успешно создан")
        
        # Тестовые данные для уведомления
        test_event = {
            "type": "receive-money",
            "client_id": "12345",
            "amount": "1000.50",
            "currency": "USD",
            "sender": "John Doe",
            "account_id": "ACC123456",
            "transaction_id": "TRX789012"
        }
        
        # Пытаемся обработать уведомление
        result = service.handle_hook(test_event)
        
        logger.info(f"Уведомление обработано: {result}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании сервиса уведомлений: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Основная функция
    """
    logger.info("Начало тестирования сервиса push-уведомлений")
    
    # Список тестовых функций
    tests = [
        ("Тестирование подключения к Firebase", test_firebase),
        ("Тестирование отправки сообщения Firebase", test_firebase_send),
        ("Тестирование сервиса уведомлений", test_notification_service)
    ]
    
    # Запуск тестов
    success_count = 0
    for name, test_func in tests:
        logger.info(f"\n=== {name} ===")
        try:
            result = test_func()
            if result:
                logger.info(f"✅ {name} - успешно")
                success_count += 1
            else:
                logger.error(f"❌ {name} - не удалось")
        except Exception as e:
            logger.error(f"❌ {name} - ошибка: {e}")
    
    # Вывод результатов тестирования
    logger.info(f"\nРезультаты тестирования: {success_count}/{len(tests)} тестов успешно")
    
    if success_count < len(tests):
        logger.warning("Не все тесты прошли успешно")
        sys.exit(1)
    else:
        logger.info("Все тесты успешно выполнены")
        sys.exit(0)

if __name__ == "__main__":
    main()
EOL
  log "simple_test.py создан."
fi

# Создаем .env файл, если его нет
if [ ! -f ".env" ]; then
  log "Создание .env файла..."
  cat > .env << 'EOL'
# Путь к файлу учетных данных Firebase
FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json

# Тестовые токены Firebase для отправки уведомлений
TEST_FCM_TOKEN=YOUR_REAL_FCM_TOKEN_HERE
TEST_FCM_TOKEN_2=ANOTHER_REAL_FCM_TOKEN_HERE

# Настройки Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_NOTIFICATION_TOPIC=notification_events
EOL
  log ".env файл создан. Не забудьте обновить токены Firebase для реальной отправки уведомлений."
fi

# Проверяем наличие файла с учетными данными Firebase
fb_credentials_file="credentials/push-service-e154f-firebase-adminsdk-fbsvc-750b157407.json"
if [ ! -f "$fb_credentials_file" ]; then
  log "ВНИМАНИЕ: Не найден файл с учетными данными Firebase по пути $fb_credentials_file"
  log "Создаю тестовый файл для демонстрации (не будет работать для реальной отправки уведомлений)"
  
  # Создаем тестовый файл с учетными данными Firebase
  cat > "$fb_credentials_file" << 'EOL'
{
  "type": "service_account",
  "project_id": "demo-project",
  "private_key_id": "demo-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIBVAIBADANBgkqhkiG9w0BAQEFAASCAT4wggE6AgEAAkEAq7BFUpkGp3+LQmlQ\nYx2eqzDV+xeG8kx/sQFV8qIw7Z5mvluEyPpJyRXLY4MFEFFJ8MbLCNYuCKTQZGSM\n+KPhXQIDAQAB\n-----END PRIVATE KEY-----",
  "client_email": "demo@demo-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/demo"
}
EOL
  log "Тестовый файл с учетными данными Firebase создан. Для реальной отправки уведомлений замените его настоящим файлом."
fi

# Запускаем Docker Compose
log "Запуск Docker Compose..."
docker-compose -f docker/docker-compose.yml up --build

# Этот код выполнится только если docker-compose завершится успешно
log "Docker Compose завершил работу."