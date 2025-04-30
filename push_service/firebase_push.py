"""
Модуль для работы с Firebase Cloud Messaging.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any

import firebase_admin
from firebase_admin import credentials, messaging

# Настройка логирования
logger = logging.getLogger("push_service")


class PushError(Exception):
    """Ошибки, связанные с отправкой push-уведомлений"""
    pass


class FirebasePushService:
    """
    Сервис для отправки push-уведомлений через Firebase Cloud Messaging.
    Реализован как синглтон для экономии ресурсов при инициализации Firebase.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls, service_account_path=None):
        """
        Получение синглтон-экземпляра сервиса
        
        Args:
            service_account_path: Путь к файлу с учетными данными Firebase
            
        Returns:
            Экземпляр FirebasePushService
        """
        if cls._instance is None:
            if service_account_path is None:
                service_account_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
            cls._instance = cls(service_account_path)
        return cls._instance
    
    def __init__(self, service_account_path: str):
        """
        Инициализация Firebase
        
        Args:
            service_account_path: Путь к JSON-файлу с учетными данными Firebase
        """
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise PushError(f"Firebase initialization error: {str(e)}")
    
    def send_push(self, 
                 token: str, 
                 title: str, 
                 body: str, 
                 data: Optional[Dict[str, str]] = None,
                 apns: Optional[Dict] = None,
                 android: Optional[Dict] = None,
                 topic: Optional[str] = None,
                 image: Optional[str] = None,
                 badge: Optional[int] = None,
                 click_action: Optional[str] = None) -> str:
        """
        Отправка push-уведомления на одно устройство
        
        Args:
            token: FCM токен устройства
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные для приложения (не отображаются)
            apns: Специфичные для iOS параметры
            android: Специфичные для Android параметры
            topic: Тема для отправки нескольким устройствам (используется вместо token)
            image: URL изображения для уведомления (Android/iOS)
            badge: Число для отображения на иконке приложения (iOS)
            click_action: Действие при клике на уведомление (URL или deeplink)
            
        Returns:
            Идентификатор отправленного сообщения
        """
        try:
            # Проверка валидности токена
            if not token and not topic:
                raise ValueError("Either token or topic must be provided")
            
            # Создание объекта уведомления
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Создание специфичной конфигурации для iOS
            apns_config = None
            if apns or badge:
                aps_dict = {
                    'alert': {
                        'title': title,
                        'body': body
                    }
                }
                
                if badge:
                    aps_dict['badge'] = badge
                
                if apns:
                    if 'sound' in apns:
                        aps_dict['sound'] = apns.get('sound')
                    if 'content_available' in apns:
                        aps_dict['content-available'] = 1 if apns.get('content_available') else 0
                    if 'mutable_content' in apns:
                        aps_dict['mutable-content'] = 1 if apns.get('mutable_content') else 0
                    if 'category' in apns:
                        aps_dict['category'] = apns.get('category')
                
                apns_config = messaging.APNSConfig(
                    headers=apns.get('headers') if apns else None,
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps.from_dict(aps_dict),
                        custom_data=apns.get('custom_data', {}) if apns else {}
                    )
                )
            
            # Создание специфичной конфигурации для Android
            android_config = None
            if android or click_action:
                android_notification = None
                if android:
                    android_notification = messaging.AndroidNotification(
                        title=title,
                        body=body,
                        icon=android.get('icon'),
                        color=android.get('color'),
                        sound=android.get('sound'),
                        tag=android.get('tag'),
                        click_action=android.get('click_action') or click_action
                    )
                else:
                    android_notification = messaging.AndroidNotification(
                        click_action=click_action
                    )
                
                android_config = messaging.AndroidConfig(
                    priority=android.get('priority', 'high') if android else 'high',
                    notification=android_notification,
                    data=android.get('data', {}) if android else {}
                )
            
            # Создание сообщения
            if topic:
                message = messaging.Message(
                    notification=notification,
                    data=data or {},
                    topic=topic,
                    apns=apns_config,
                    android=android_config
                )
            else:
                message = messaging.Message(
                    notification=notification,
                    data=data or {},
                    token=token,
                    apns=apns_config,
                    android=android_config
                )
            
            # Отправка сообщения
            response = messaging.send(message)
            logger.info(f"Push notification sent: {response}")
            return response
            
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            raise PushError(f"Invalid parameters: {str(ve)}")
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            raise PushError(f"Push notification failed: {str(e)}")
    
    def send_multicast(self, 
                      tokens: List[str], 
                      title: str, 
                      body: str, 
                      data: Optional[Dict[str, str]] = None,
                      apns: Optional[Dict] = None,
                      android: Optional[Dict] = None) -> Dict:
        """
        Отправка push-уведомления на несколько устройств
        
        Args:
            tokens: Список FCM токенов устройств
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные для приложения (не отображаются)
            apns: Специфичные для iOS параметры
            android: Специфичные для Android параметры
            
        Returns:
            Результаты отправки с количеством успешных и неуспешных сообщений
        """
        try:
            # Проверка валидности токенов
            if not tokens or not isinstance(tokens, list) or len(tokens) == 0:
                raise ValueError("Invalid FCM tokens list")
            
            # Создание объекта уведомления
            notification = messaging.Notification(
                title=title,
                body=body
            )
            
            # Создание конфигурации для iOS
            apns_config = None
            if apns:
                apns_config = messaging.APNSConfig(
                    headers=apns.get('headers'),
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body
                            ),
                            badge=apns.get('badge'),
                            sound=apns.get('sound', 'default'),
                            content_available=apns.get('content_available', False),
                            mutable_content=apns.get('mutable_content', False),
                            category=apns.get('category')
                        ),
                        custom_data=apns.get('custom_data', {})
                    )
                )
            
            # Создание конфигурации для Android
            android_config = None
            if android:
                android_config = messaging.AndroidConfig(
                    priority=android.get('priority', 'high'),
                    notification=messaging.AndroidNotification(
                        title=title,
                        body=body,
                        icon=android.get('icon'),
                        color=android.get('color'),
                        sound=android.get('sound'),
                        tag=android.get('tag'),
                        click_action=android.get('click_action')
                    ),
                    data=android.get('data', {})
                )
            
            # Создание мультикаст сообщения
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens,
                apns=apns_config,
                android=android_config
            )
            
            # Отправка сообщения
            response = messaging.send_multicast(message)
            
           
            logger.info(f"Multicast sent: {response.success_count} successful, {response.failure_count} failed")
            
            # Анализ ошибок
            failed_tokens = []
            message_ids = []
            
            for idx, resp in enumerate(response.responses):
                if resp.success:
                    message_ids.append(resp.message_id)
                else:
                    failed_tokens.append({
                        "token": tokens[idx],
                        "error": str(resp.exception)
                    })
                    logger.warning(f"Failed to send to token {tokens[idx]}: {resp.exception}")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "message_ids": message_ids,
                "failed_tokens": failed_tokens
            }
            
        except ValueError as ve:
            logger.error(f"Value error: {ve}")
            raise PushError(f"Invalid parameters: {str(ve)}")
        except Exception as e:
            logger.error(f"Error sending multicast push: {e}")
            raise PushError(f"Multicast push failed: {str(e)}")


class FirebaseMessaging:
    """Класс для работы с Firebase Cloud Messaging"""
    
    def __init__(self, credentials_path: str = "serviceAccountKey.json"):
        """
        Инициализирует Firebase с указанными учетными данными.
        
        Args:
            credentials_path: Путь к файлу с учетными данными Firebase
        """
        try:
            logger.info(f"Файл учетных данных Firebase найден: {credentials_path}")
            self.service = FirebasePushService(credentials_path)
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            raise PushError(f"Failed to initialize Firebase: {str(e)}")
    
    def send_push(self, 
                  token: str, 
                  title: str, 
                  body: str, 
                  data: Optional[Dict[str, str]] = None, 
                  topic: Optional[str] = None,
                  image: Optional[str] = None,
                  badge: Optional[int] = None,
                  click_action: Optional[str] = None
                 ) -> str:
        """
        Отправляет push-уведомление на устройство.
        
        Args:
            token: FCM токен устройства
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные для передачи с уведомлением (не отображаются)
            topic: Тема для отправки нескольким устройствам (используется вместо token)
            image: URL изображения для уведомления (Android/iOS)
            badge: Число для отображения на иконке приложения (iOS)
            click_action: Действие при клике на уведомление (URL или deeplink)
            
        Returns:
            message_id: Идентификатор отправленного сообщения
        """
        # Настройки для Android
        android_config = {
            'priority': 'high',
            'icon': 'stock_ticker_update',
            'color': '#f45342',
            'click_action': click_action
        }
        
        # Настройки для iOS
        apns_config = {
            'badge': badge,
            'sound': 'default',
            'content_available': True
        }
        
        return self.service.send_push(
            token=token,
            title=title,
            body=body,
            data=data,
            topic=topic,
            image=image,
            android=android_config,
            apns=apns_config
        )
    
    def send_multicast(self, 
                       tokens: List[str], 
                       title: str, 
                       body: str, 
                       data: Optional[Dict[str, str]] = None,
                       **kwargs
                      ) -> Dict[str, Any]:
        """
        Отправляет push-уведомление на несколько устройств.
        
        Args:
            tokens: Список FCM токенов устройств
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные для передачи с уведомлением
            **kwargs: Дополнительные параметры для уведомления
            
        Returns:
            response: Результат отправки с информацией об успешных и неудачных доставках
        """
        # Настройки для Android
        android_config = {
            'priority': 'high',
            'icon': 'stock_ticker_update',
            'color': '#f45342',
            'click_action': kwargs.get('click_action')
        }
        
        # Настройки для iOS
        apns_config = {
            'badge': kwargs.get('badge'),
            'sound': 'default',
            'content_available': True
        }
        
        return self.service.send_multicast(
            tokens=tokens,
            title=title,
            body=body,
            data=data,
            android=android_config,
            apns=apns_config
        )
    
    def subscribe_to_topic(self, tokens: Union[str, List[str]], topic: str) -> Dict[str, Any]:
        """
        Подписывает токены на тему.
        
        Args:
            tokens: FCM токен устройства или список токенов
            topic: Название темы
            
        Returns:
            response: Результат подписки
        """
        try:
            # Если передан один токен, оборачиваем его в список
            if isinstance(tokens, str):
                tokens = [tokens]
                
            response = messaging.subscribe_to_topic(tokens, topic)
            
            result = {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(err) for err in getattr(response, 'errors', [])]
            }
            
            logger.info(f"Subscribed to topic '{topic}'. Success: {response.success_count}, Failure: {response.failure_count}")
            return result
            
        except Exception as e:
            logger.error(f"Error subscribing to topic '{topic}': {str(e)}")
            raise PushError(f"Topic subscription failed: {str(e)}")
            
    def unsubscribe_from_topic(self, tokens: Union[str, List[str]], topic: str) -> Dict[str, Any]:
        """
        Отписывает токены от темы.
        
        Args:
            tokens: FCM токен устройства или список токенов
            topic: Название темы
            
        Returns:
            response: Результат отписки
        """
        try:
            # Если передан один токен, оборачиваем его в список
            if isinstance(tokens, str):
                tokens = [tokens]
                
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            result = {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(err) for err in getattr(response, 'errors', [])]
            }
            
            logger.info(f"Unsubscribed from topic '{topic}'. Success: {response.success_count}, Failure: {response.failure_count}")
            return result
            
        except Exception as e:
            logger.error(f"Error unsubscribing from topic '{topic}': {str(e)}")
            raise PushError(f"Topic unsubscription failed: {str(e)}")