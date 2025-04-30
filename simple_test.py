#!/usr/bin/env python3
import os
import logging
import json
from typing import Dict, Any, Optional

from push_service import NotificationService
from push_service.firebase_push import FirebaseMessaging, PushError


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем тестовый FCM токен из переменной окружения или используем фиктивный токен
TEST_FCM_TOKEN = os.environ.get("TEST_FCM_TOKEN", "dummy_fcm_token_for_testing")

def test_firebase_connection():
    """Тестирует подключение к Firebase"""
    logger.info("=== Тестирование подключения к Firebase ===")
    try:
        firebase = FirebaseMessaging()
        logger.info("Firebase успешно инициализирован")
        logger.info("✅ Тестирование подключения к Firebase - успешно")
        return firebase
    except Exception as e:
        logger.error(f"Ошибка при инициализации Firebase: {str(e)}")
        logger.error("❌ Тестирование подключения к Firebase - не удалось")
        return None

def test_firebase_send(firebase: FirebaseMessaging):
    """Тестирует отправку сообщения через Firebase"""
    logger.info("=== Тестирование отправки сообщения Firebase ===")
    
    # Проверка наличия токена для тестирования
    if not TEST_FCM_TOKEN or TEST_FCM_TOKEN == "dummy_fcm_token_for_testing":
        logger.warning("Переменная TEST_FCM_TOKEN не установлена, используется тестовый токен")
    
    try:
        # Отправляем тестовое уведомление
        result = firebase.send_push(
            token=TEST_FCM_TOKEN,
            title="Тестовое уведомление",
            body="Это тестовое сообщение от сервиса push-уведомлений",
            data={
                "type": "test",
                "timestamp": "2025-04-30T12:00:00",
                "target_screen": "main"
            }
        )
        logger.info(f"Сообщение успешно отправлено, ID: {result}")
        logger.info("✅ Тестирование отправки сообщения Firebase - успешно")
        return True
    except PushError as e:
        logger.error(f"Ошибка при отправке сообщения: {str(e)}")
        logger.error("❌ Тестирование отправки сообщения Firebase - не удалось")
        return False

def test_notification_service():
    """Тестирует сервис уведомлений"""
    logger.info("=== Тестирование сервиса уведомлений ===")
    
    try:
        # Инициализируем сервис уведомлений
        service = NotificationService()
        logger.info("Сервис уведомлений успешно создан")
        
        # Создаем тестовый вебхук для типа "receive-money"
        test_hook = {
            "type": "receive-money",
            "client_id": "test-client-123",
            "amount": 1000.50,
            "currency": "RUB",
            "sender_name": "John Doe",
            "account_id": "acc-789",
            "transaction_id": "tx-456",
            "fcm_token": TEST_FCM_TOKEN  # Используем тестовый токен
        }
        
        # Вызываем обработчик вебхука
        result = service.handle_hook(test_hook)
        logger.info(f"Уведомление обработано: {result}")
        
        logger.info("✅ Тестирование сервиса уведомлений - успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании сервиса уведомлений: {str(e)}")
        logger.error("❌ Тестирование сервиса уведомлений - не удалось")
        return False

def test_all_notification_types():
    """Тестирует все типы уведомлений"""
    logger.info("=== Тестирование всех типов уведомлений ===")
    
    # Инициализируем сервис
    service = NotificationService()
    
    # Список тестовых хуков для разных типов уведомлений
    test_hooks = [
        {
            "type": "receive-money",
            "client_id": "test-client-123",
            "amount": 1000.50,
            "currency": "RUB",
            "sender_name": "John Doe",
            "account_id": "acc-789",
            "transaction_id": "tx-456",
            "fcm_token": TEST_FCM_TOKEN
        },
        {
            "type": "send-money",
            "client_id": "test-client-123",
            "amount": 500.75,
            "currency": "USD",
            "recipient_name": "Jane Smith",
            "account_id": "acc-789",
            "transaction_id": "tx-457",
            "fcm_token": TEST_FCM_TOKEN
        },
        {
            "type": "account-activated",
            "client_id": "test-client-123",
            "account_id": "acc-790",
            "account_type": "premium",
            "fcm_token": TEST_FCM_TOKEN
        },
        {
            "type": "client-status-changed",
            "client_id": "test-client-123",
            "old_status": "standard",
            "new_status": "verified",
            "fcm_token": TEST_FCM_TOKEN
        }
    ]
    
    results = {}
    
    # Тестируем каждый тип уведомления
    for hook in test_hooks:
        hook_type = hook["type"]
        try:
            logger.info(f"Тестирование типа уведомления: {hook_type}")
            result = service.handle_hook(hook)
            success = result is not None and getattr(result, 'success', False)
            
            if success:
                logger.info(f"✅ Уведомление типа {hook_type} успешно обработано")
            else:
                logger.warning(f"⚠️ Уведомление типа {hook_type} обработано с ошибкой")
                
            results[hook_type] = success
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке уведомления типа {hook_type}: {str(e)}")
            results[hook_type] = False
    
    # Выводим общий результат
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info(f"Результат тестирования всех типов: {success_count}/{total_count} успешно")
    
    return results

def save_service_worker():
    """Сохраняет Service Worker для Firebase Messaging"""
    logger.info("=== Создание Service Worker для Firebase Messaging ===")
    
    # Проверяем наличие файла firebase-messaging-sw.js
    if os.path.exists("firebase-messaging-sw.js"):
        logger.info("Файл firebase-messaging-sw.js уже существует")
        return True
    
    try:
        # Базовый код для Service Worker
        sw_code = """
// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/11.6.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/11.6.1/firebase-messaging-compat.js');

// Firebase конфигурация
firebase.initializeApp({
    apiKey: "AIzaSyDNPFZbRyLAOBt1iCZ8xAkL8IC8tMIGj_Y",
    authDomain: "push-service-e154f.firebaseapp.com",
    projectId: "push-service-e154f",
    storageBucket: "push-service-e154f.firebasestorage.app",
    messagingSenderId: "679184734382",
    appId: "1:679184734382:web:83a0dfc8347034f084f53f"
});

const messaging = firebase.messaging();

// Обработка сообщений, полученных в фоновом режиме
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Получено сообщение в фоновом режиме:', payload);
    
    const notificationTitle = payload.notification.title || 'Новое уведомление';
    const notificationOptions = {
        body: payload.notification.body || 'У вас новое сообщение',
        icon: '/path/to/icon.png',
        data: payload.data
    };
    
    return self.registration.showNotification(notificationTitle, notificationOptions);
});
        """
        
        # Сохраняем файл
        with open("firebase-messaging-sw.js", "w") as f:
            f.write(sw_code)
        
        logger.info("✅ Service Worker успешно создан")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при создании Service Worker: {str(e)}")
        return False

def main():
    """Основная функция для тестирования сервиса push-уведомлений"""
    logger.info("Начало тестирования сервиса push-уведомлений")
    
    # Тестируем подключение к Firebase
    firebase = test_firebase_connection()
    if not firebase:
        logger.error("Тестирование остановлено из-за ошибки подключения к Firebase")
        return
    
    # Тестируем отправку сообщения Firebase
    send_success = test_firebase_send(firebase)
    
    # Тестируем сервис уведомлений
    service_success = test_notification_service()
    
    # Создаем Service Worker для веб-пушей
    sw_success = save_service_worker()
    
    # Опционально: тестируем все типы уведомлений
    # all_types_results = test_all_notification_types()
    
    # Выводим общий результат
    success_count = sum([firebase is not None, send_success, service_success])
    logger.info("")
    logger.info(f"Результаты тестирования: {success_count}/3 тестов успешно")
    
    if success_count < 3:
        logger.warning("Не все тесты прошли успешно")
        exit(1)
    else:
        logger.info("Все тесты успешно пройдены")
        exit(0)

if __name__ == "__main__":
    main()