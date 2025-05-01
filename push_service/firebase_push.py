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
        try:
            # Проверяем, инициализировано ли уже приложение
            try:
                self.app = firebase_admin.get_app()
                logging.info("Используется существующее Firebase приложение")
            except ValueError:
                # Приложение не инициализировано, инициализируем его
                if service_account_path is None:
                    service_account_path = os.environ.get(
                        'FIREBASE_CREDENTIALS_PATH', 
                        'credentials/serviceAccountKey.json'
                    )
                
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
            
        # Преобразуем все значения в data в строки
        string_data = {}
        for key, value in data.items():
            string_data[key] = str(value)
        
        success_count = 0
        failure_count = 0
        errors = []
        
        # Отправляем отдельное сообщение для каждого токена
        for token in tokens:
            try:
                # Создаем объект сообщения (по документации)
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data=string_data,
                    token=token
                )
                
                # Отправляем сообщение
                response = messaging.send(message)
                logging.info(f"Сообщение успешно отправлено: {response}")
                success_count += 1
            except Exception as e:
                logging.error(f"Ошибка отправки сообщения на токен {token}: {e}")
                failure_count += 1
                errors.append({
                    "token": token,
                    "error": str(e)
                })
        
        # Формируем результат
        result = {
            "success": success_count,
            "failure": failure_count,
            "total": len(tokens)
        }
        
        if errors:
            result["errors"] = errors
        
        return result