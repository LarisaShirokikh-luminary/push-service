"""
Пример интеграции сервиса push-уведомлений с Kafka.

Этот скрипт показывает, как использовать сервис уведомлений
для обработки событий из Kafka.
"""

import os
import json
import logging
import signal
import sys
from typing import Dict, Any

from dotenv import load_dotenv
from kafka import KafkaConsumer

from push_service import NotificationService

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("kafka_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("kafka_integration")


class KafkaNotificationConsumer:
    """
    Консьюмер Kafka для обработки событий уведомлений.
    """
    def __init__(self, bootstrap_servers: str, topic: str, service_account_path: str, db_connection):
        """
        Инициализация консьюмера Kafka.
        
        Args:
            bootstrap_servers: Список серверов Kafka
            topic: Тема Kafka для подписки
            service_account_path: Путь к файлу учетных данных Firebase
            db_connection: Соединение с базой данных
        """
        self.is_running = False
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        
        # Инициализация сервиса уведомлений
        self.notification_service = NotificationService(
            db=db_connection,
            service_account_path=service_account_path
        )
        
        # Инициализация консьюмера Kafka
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='notification_service_group'
        )
        
        logger.info(f"Initialized Kafka consumer for topic: {self.topic}")
    
    def start(self):
        """Запуск обработки сообщений из Kafka."""
        logger.info("Starting Kafka consumer...")
        self.is_running = True
        
        # Обработка сигналов завершения
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
        # Бесконечный цикл обработки сообщений
        try:
            for message in self.consumer:
                if not self.is_running:
                    break
                
                self.process_message(message)
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
        finally:
            self.consumer.close()
            logger.info("Kafka consumer stopped")
    
    def process_message(self, message):
        """
        Обработка сообщения из Kafka.
        
        Args:
            message: Сообщение Kafka
        """
        try:
            logger.info(f"Received message: {message.topic} - {message.partition} - {message.offset}")
            
            # Получение данных сообщения
            data = message.value
            
            # Логирование информации о событии
            event_type = data.get('type')
            client_id = data.get('client_id')
            logger.info(f"Processing event: {event_type} for client {client_id}")
            
            # Обработка события уведомления
            result = self.notification_service.handle_hook(data)
            
            if result:
                logger.info(f"Notification sent: {result}")
            else:
                logger.warning("Failed to send notification")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def stop(self, signum=None, frame=None):
        """Остановка консьюмера."""
        logger.info("Stopping Kafka consumer...")
        self.is_running = False


def create_mock_db():
    """
    Создание мок-объекта базы данных для примера.
    В реальном приложении здесь будет инициализация соединения
    с настоящей базой данных.
    """
    from push_service.models import MockClient
    
    # Создаем мок-клиентов
    clients = {
        "12345": MockClient(
            core_id="12345",
            firebase_token=os.environ.get("TEST_FCM_TOKEN", "test_token_1"),
            language="en",
        ),
        "67890": MockClient(
            core_id="67890",
            firebase_token=os.environ.get("TEST_FCM_TOKEN_2", "test_token_2"),
            language="ru",
        )
    }
    
    # Имитируем структуру базы данных
    class MockDB:
        def __init__(self, clients):
            self.clients = clients
            self.client = self
        
        def get_by_core_id(self, core_id):
            return self.clients.get(core_id)
    
    return MockDB(clients)


def main():
    """Основная функция."""
    try:
        # Получение настроек из переменных окружения
        bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        topic = os.environ.get('KAFKA_NOTIFICATION_TOPIC', 'notification_events')
        service_account_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
        
        # Создание мок-БД
        mock_db = create_mock_db()
        
        # Создание и запуск консьюмера
        consumer = KafkaNotificationConsumer(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            service_account_path=service_account_path,
            db_connection=mock_db
        )
        
        # Запуск обработки сообщений
        consumer.start()
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()