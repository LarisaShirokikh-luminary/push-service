# Файл: push_service/models.py
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class PushNotificationStatus(Enum):
    """Статус отправки push-уведомления."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


@dataclass
class PushNotification:
    """Модель push-уведомления."""
    id: Optional[str] = None
    title: str = ""
    body: str = ""
    tokens: List[str] = None
    data: Dict = None
    status: PushNotificationStatus = PushNotificationStatus.PENDING
    success_count: int = 0
    failure_count: int = 0
    error_details: List[Dict] = None
    
    def __post_init__(self):
        if self.tokens is None:
            self.tokens = []
        if self.data is None:
            self.data = {}
        if self.error_details is None:
            self.error_details = []
            
    def to_dict(self) -> Dict:
        """Преобразование объекта в словарь."""
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "tokens": self.tokens,
            "data": self.data,
            "status": self.status.value,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error_details": self.error_details
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PushNotification':
        """Создание объекта из словаря."""
        status_value = data.get("status", PushNotificationStatus.PENDING.value)
        status = PushNotificationStatus(status_value)
        
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            body=data.get("body", ""),
            tokens=data.get("tokens", []),
            data=data.get("data", {}),
            status=status,
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            error_details=data.get("error_details", [])
        )