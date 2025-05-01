# Файл: push_service/firebase_push.py
import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
import logging
from typing import Dict, List, Optional, Union


class FirebasePushService:
    """Сервис для отправки push-уведомлений через Firebase Cloud Messaging."""
    
    def __init__(self, service_account_path: str = None):
        """
        Инициализация сервиса Firebase.
        
        Args:
            service_account_path: Путь к файлу с учетными данными Firebase.
        """
        if service_account_path is None:
            service_account_path = os.environ.get(
                'FIREBASE_CREDENTIALS_PATH', 
                'credentials/serviceAccountKey.json'
            )
        
        try:
            cred = credentials.Certificate(service_account_path)
            self.app = firebase_admin.initialize_app(cred)
            logging.info("Firebase приложение успешно инициализировано")
        except Exception as e:
            logging.error(f"Ошибка инициализации Firebase: {e}")
            raise
    
    def send_push(
        self, 
        tokens: Union[str, List[str]], 
        title: str, 
        body: str, 
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Отправка push-уведомления.
        
        Args:
            tokens: Токен устройства или список токенов
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные для уведомления
        
        Returns:
            Dict: Результат отправки
        """
        if isinstance(tokens, str):
            tokens = [tokens]
        
        if not data:
            data = {}
            
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data,
            tokens=tokens
        )
        
        try:
            response = messaging.send_multicast(message)
            logging.info(f"Отправлено {response.success_count} сообщений из {len(tokens)}")
            
            result = {
                "success": response.success_count,
                "failure": response.failure_count,
                "total": len(tokens)
            }
            
            if response.failure_count > 0:
                result["errors"] = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        result["errors"].append({
                            "token": tokens[idx],
                            "error": str(resp.exception)
                        })
            
            return result
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления: {e}")
            return {
                "success": 0,
                "failure": len(tokens),
                "total": len(tokens),
                "errors": [{"error": str(e)}]
            }