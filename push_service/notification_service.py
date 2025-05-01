# Файл: push_service/notification_service.py
from typing import Dict, List, Optional
import uuid
import logging
from .models import PushNotification, PushNotificationStatus
from .firebase_push import FirebasePushService


class NotificationService:
    """Сервис для работы с уведомлениями."""
    
    def __init__(self, push_service: Optional[FirebasePushService] = None):
        """
        Инициализация сервиса уведомлений.
        
        Args:
            push_service: Сервис для отправки push-уведомлений.
        """
        if push_service is None:
            self.push_service = FirebasePushService()
        else:
            self.push_service = push_service
            
        self.notifications: Dict[str, PushNotification] = {}
    
    def create_notification(
        self, 
        title: str, 
        body: str, 
        tokens: List[str], 
        data: Optional[Dict] = None
    ) -> PushNotification:
        """
        Создание нового уведомления.
        
        Args:
            title: Заголовок уведомления
            body: Текст уведомления
            tokens: Список токенов устройств
            data: Дополнительные данные
        
        Returns:
            PushNotification: Созданное уведомление
        """
        notification_id = str(uuid.uuid4())
        notification = PushNotification(
            id=notification_id,
            title=title,
            body=body,
            tokens=tokens,
            data=data or {}
        )
        
        self.notifications[notification_id] = notification
        logging.info(f"Создано новое уведомление с ID: {notification_id}")
        
        return notification
    
    def send_notification(self, notification_id: str) -> PushNotification:
        """
        Отправка уведомления.
        
        Args:
            notification_id: ID уведомления для отправки
        
        Returns:
            PushNotification: Обновленное уведомление с результатами отправки
        """
        notification = self.notifications.get(notification_id)
        if not notification:
            logging.error(f"Уведомление с ID {notification_id} не найдено")
            raise ValueError(f"Уведомление с ID {notification_id} не найдено")
        
        if not notification.tokens:
            notification.status = PushNotificationStatus.FAILED
            notification.error_details = [{"error": "Не указаны токены устройств"}]
            return notification
        
        result = self.push_service.send_push(
            tokens=notification.tokens,
            title=notification.title,
            body=notification.body,
            data=notification.data
        )
        
        notification.success_count = result.get("success", 0)
        notification.failure_count = result.get("failure", 0)
        
        if notification.failure_count > 0:
            notification.error_details = result.get("errors", [])
            
        if notification.success_count > 0:
            if notification.failure_count > 0:
                notification.status = PushNotificationStatus.SENT
            else:
                notification.status = PushNotificationStatus.DELIVERED
        else:
            notification.status = PushNotificationStatus.FAILED
            
        return notification
        
    def get_notification(self, notification_id: str) -> Optional[PushNotification]:
        """
        Получение уведомления по ID.
        
        Args:
            notification_id: ID уведомления
        
        Returns:
            Optional[PushNotification]: Найденное уведомление или None
        """
        return self.notifications.get(notification_id)
    
    def list_notifications(self) -> List[PushNotification]:
        """
        Получение списка всех уведомлений.
        
        Returns:
            List[PushNotification]: Список уведомлений
        """
        return list(self.notifications.values())