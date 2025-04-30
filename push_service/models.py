"""
Модели данных для сервиса push-уведомлений.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class Client:
    """Базовый класс для клиента"""
    id: str
    core_id: str
    firebase_token: Optional[str] = None
    language: str = "en"
    notification_settings: Dict[str, bool] = field(default_factory=lambda: {"enabled": True})
    
    def __post_init__(self):
        """Валидация после создания объекта"""
        if not self.id:
            raise ValueError("Client ID cannot be empty")
        if not self.core_id:
            raise ValueError("Core ID cannot be empty")


@dataclass
class MockClient(Client):
    """Мок-класс клиента для тестирования"""
    def __init__(self, core_id: str, firebase_token: Optional[str] = None, language: str = "en"):
        super().__init__(
            id=core_id,
            core_id=core_id,
            firebase_token=firebase_token or "sample_token_for_testing",
            language=language,
            notification_settings={"enabled": True}
        )


@dataclass
class NotificationData:
    """Данные для отправки уведомления"""
    token: str
    title: str
    body: str
    data: Dict[str, Any] = field(default_factory=dict)
    android: Dict[str, Any] = field(default_factory=dict)
    apns: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Валидация после создания объекта"""
        if not self.token:
            raise ValueError("Firebase token cannot be empty")
        if not self.title:
            raise ValueError("Notification title cannot be empty")
        if not self.body:
            raise ValueError("Notification body cannot be empty")


@dataclass
class NotificationResult:
    """Результат отправки уведомления"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class MulticastResult:
    """Результат групповой отправки уведомлений"""
    success_count: int
    failure_count: int
    message_ids: List[str] = field(default_factory=list)
    failed_tokens: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PushNotification:
    """Модель для push-уведомления"""
    
    token: str  # FCM токен устройства
    title: str  # Заголовок уведомления
    body: str   # Текст уведомления
    data: Optional[Dict[str, str]] = None  # Дополнительные данные (не отображаются)
    topic: Optional[str] = None  # Тема для отправки нескольким устройствам
    image: Optional[str] = None  # URL изображения для уведомления
    badge: Optional[int] = None  # Число для отображения на иконке приложения (iOS)
    click_action: Optional[str] = None  # Действие при клике (URL или deeplink)
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if not self.token and not self.topic:
            raise ValueError("Either token or topic must be provided")
        
        # Конвертация всех значений в data в строки (требование Firebase)
        if self.data:
            self.data = {k: str(v) for k, v in self.data.items()}