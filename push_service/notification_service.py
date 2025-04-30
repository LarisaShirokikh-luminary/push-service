"""
Сервис для обработки и отправки уведомлений различных типов.
"""

import logging
from typing import Dict, Any, Optional, Type

from .firebase_push import FirebaseMessaging, PushError
from .models import Client, MockClient, NotificationResult
from .handlers import NotificationHandler, MoneyReceivedHandler, MoneySentHandler, AccountActivatedHandler, StatusChangedHandler

# Настройка логирования
logger = logging.getLogger("push_service")

class NotificationService:
    """
    Сервис для обработки различных типов уведомлений.
    
    Отвечает за:
    - Выбор подходящего обработчика для типа уведомления
    - Создание клиента на основе данных запроса
    - Делегирование обработки уведомления соответствующему обработчику
    - Отправку уведомления через Firebase
    """
    
    def __init__(self, credentials_path: str = "serviceAccountKey.json"):
        """
        Инициализация сервиса уведомлений.
        
        Args:
            credentials_path: Путь к учетным данным Firebase
        """
        self.firebase = FirebaseMessaging(credentials_path=credentials_path)
        self.handlers = self._register_handlers()
        logger.info(f"Registered handlers: {list(self.handlers.keys())}")
    
    def _register_handlers(self) -> Dict[str, Type[NotificationHandler]]:
        """
        Регистрирует обработчики для различных типов уведомлений.
        
        Returns:
            Словарь с типами уведомлений и соответствующими обработчиками
        """
        return {
            'receive-money': MoneyReceivedHandler,
            'send-money': MoneySentHandler,
            'account-activated': AccountActivatedHandler,
            'client-status-changed': StatusChangedHandler
        }
    
    def handle_hook(self, hook_data: Dict[str, Any]) -> Optional[NotificationResult]:
        """
        Обрабатывает webhook-запрос и отправляет уведомление.
        
        Args:
            hook_data: Данные webhook-запроса
            
        Returns:
            Результат отправки уведомления или None в случае ошибки
        """
        if not hook_data:
            logger.error("handle_hook: No webhook data received")
            return None
        
        logger.info("handle_hook: Webhook received")
        
        # Получаем тип уведомления
        notification_type = hook_data.get('type')
        if not notification_type:
            logger.error("handle_hook: Notification type not specified")
            return None
        
        # Находим обработчик для данного типа уведомления
        handler_class = self.handlers.get(notification_type)
        if not handler_class:
            logger.error(f"handle_hook: No handler found for notification type '{notification_type}'")
            return None
        
        try:
            # Создаем моковый объект клиента для тестирования
            client = self._create_test_client(hook_data)
            
            # Создаем экземпляр обработчика
            handler = handler_class(db=None)  # Передаем None вместо объекта БД для тестирования
            
            # Обрабатываем уведомление
            notification_data = handler.process(client, hook_data)
            
            # Отправляем уведомление
            if not notification_data:
                logger.warning("handle_hook: Handler returned no data")
                return None
            
            # Отправляем push-уведомление
            response = self.firebase.send_push(
                token=notification_data.get('token'),
                title=notification_data.get('title'),
                body=notification_data.get('body'),
                data=notification_data.get('data'),
                android=notification_data.get('android'),
                apns=notification_data.get('apns')
            )
            
            # Возвращаем результат
            return NotificationResult(
                success=True,
                message_id=response
            )
        
        except PushError as e:
            logger.error(f"handle_hook: Push notification error: {e}")
            return NotificationResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"handle_hook: Unexpected error: {e}")
            return NotificationResult(
                success=False,
                error=str(e)
            )
    
    def _create_test_client(self, data: Dict[str, Any]) -> Client:
        """
        Создает тестовый объект клиента на основе данных запроса.
        
        Args:
            data: Данные запроса
            
        Returns:
            Объект клиента
        """
        client_id = data.get('client_id', 'test-client')
        fcm_token = data.get('fcm_token', 'test-token')
        language = data.get('language', 'en')
        
        return MockClient(
            core_id=client_id,
            firebase_token=fcm_token,
            language=language
        )