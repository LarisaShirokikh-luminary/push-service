#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

from push_service.firebase_push import FirebaseMessaging, PushError
from push_service.handlers import NotificationService
from push_service.models import PushNotification

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_push(args):
    """Отправляет push-уведомление"""
    try:
        # Инициализируем Firebase
        firebase = FirebaseMessaging(credentials_path=args.credentials)
        
        # Подготавливаем дополнительные данные
        data = {}
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError:
                logger.error("Ошибка: Неверный формат JSON в параметре --data")
                return 1
        
        # Если указан файл с данными, читаем из него
        if args.data_file:
            try:
                with open(args.data_file, 'r') as f:
                    file_data = json.load(f)
                    data.update(file_data)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Ошибка при чтении файла данных: {e}")
                return 1
        
        # Отправляем уведомление
        response = firebase.send_push(
            token=args.token,
            title=args.title,
            body=args.body,
            data=data,
            topic=args.topic,
            image=args.image,
            badge=args.badge,
            click_action=args.click_action
        )
        
        logger.info(f"Уведомление успешно отправлено! ID: {response}")
        return 0
        
    except PushError as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
        return 1
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return 1

def handle_hook(args):
    """Обрабатывает webhook-запрос"""
    try:
        # Инициализируем сервис уведомлений
        notification_service = NotificationService(credentials_path=args.credentials)
        
        # Получаем данные webhook
        hook_data = {}
        
        # Если указан файл с данными, читаем из него
        if args.hook_file:
            try:
                with open(args.hook_file, 'r') as f:
                    hook_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Ошибка при чтении файла webhook: {e}")
                return 1
        # Иначе пытаемся прочитать из аргумента --hook-data
        elif args.hook_data:
            try:
                hook_data = json.loads(args.hook_data)
            except json.JSONDecodeError:
                logger.error("Ошибка: Неверный формат JSON в параметре --hook-data")
                return 1
        else:
            logger.error("Необходимо указать параметр --hook-file или --hook-data")
            return 1
        
        # Обрабатываем webhook
        result = notification_service.handle_hook(hook_data)
        
        if result and result.success:
            logger.info(f"Уведомление успешно отправлено! ID: {result.message_id}")
            return 0
        elif result:
            logger.error(f"Ошибка отправки уведомления: {result.error}")
            return 1
        else:
            logger.warning("Уведомление не требуется или произошла ошибка")
            return 1
            
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return 1

def subscribe_topic(args):
    """Подписывает токен на тему"""
    try:
        # Инициализируем Firebase
        firebase = FirebaseMessaging(credentials_path=args.credentials)
        
        # Подписываем токены на тему
        tokens = args.tokens.split(',')
        result = firebase.subscribe_to_topic(tokens, args.topic)
        
        logger.info(f"Успешно подписано токенов: {result['success_count']}")
        if result['failure_count'] > 0:
            logger.warning(f"Не удалось подписать токенов: {result['failure_count']}")
            for error in result['errors']:
                logger.warning(f"Ошибка: {error}")
                
        return 0 if result['success_count'] > 0 else 1
        
    except PushError as e:
        logger.error(f"Ошибка подписки на тему: {e}")
        return 1
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return 1

def unsubscribe_topic(args):
    """Отписывает токен от темы"""
    try:
        # Инициализируем Firebase
        firebase = FirebaseMessaging(credentials_path=args.credentials)
        
        # Отписываем токены от темы
        tokens = args.tokens.split(',')
        result = firebase.unsubscribe_from_topic(tokens, args.topic)
        
        logger.info(f"Успешно отписано токенов: {result['success_count']}")
        if result['failure_count'] > 0:
            logger.warning(f"Не удалось отписать токенов: {result['failure_count']}")
            for error in result['errors']:
                logger.warning(f"Ошибка: {error}")
                
        return 0 if result['success_count'] > 0 else 1
        
    except PushError as e:
        logger.error(f"Ошибка отписки от темы: {e}")
        return 1
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return 1

def simulate_notification(args):
    """Имитирует отправку уведомления для тестирования"""
    try:
        # Инициализируем сервис уведомлений
        notification_service = NotificationService(credentials_path=args.credentials)
        
        # Создаем тестовый webhook в зависимости от типа уведомления
        hook_type = args.type
        
        # Базовые данные для всех типов уведомлений
        hook_data = {
            "type": hook_type,
            "client_id": args.client_id,
            "fcm_token": args.token
        }
        
        # Дополнительные данные в зависимости от типа уведомления
        if hook_type == "receive-money":
            hook_data.update({
                "amount": args.amount or 1000.0,
                "currency": args.currency or "RUB",
                "sender_name": args.sender or "Отправитель",
                "account_id": args.account_id or "acc-123",
                "transaction_id": f"tx-{int(time.time())}"
            })
        elif hook_type == "send-money":
            hook_data.update({
                "amount": args.amount or 500.0,
                "currency": args.currency or "RUB",
                "recipient_name": args.recipient or "Получатель",
                "account_id": args.account_id or "acc-123",
                "transaction_id": f"tx-{int(time.time())}"
            })
        elif hook_type == "account-activated":
            hook_data.update({
                "account_id": args.account_id or "acc-123",
                "account_type": args.account_type or "standard"
            })
        elif hook_type == "client-status-changed":
            hook_data.update({
                "old_status": args.old_status or "standard",
                "new_status": args.new_status or "verified"
            })
        
        # Обрабатываем webhook
        result = notification_service.handle_hook(hook_data)
        
        if result and result.success:
            logger.info(f"Тестовое уведомление успешно отправлено! ID: {result.message_id}")
            return 0
        elif result:
            logger.error(f"Ошибка отправки тестового уведомления: {result.error}")
            return 1
        else:
            logger.warning("Тестовое уведомление не требуется или произошла ошибка")
            return 1
            
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return 1

def main():
    """Основная функция CLI"""
    # Создаем основной парсер
    parser = argparse.ArgumentParser(
        description="Утилита для управления push-уведомлениями",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Общие аргументы
    parser.add_argument(
        "--credentials", "-c",
        default=os.environ.get("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json"),
        help="Путь к файлу учетных данных Firebase"
    )
    
    # Создаем подпарсеры для разных команд
    subparsers = parser.add_subparsers(
        title="Команды",
        dest="command",
        help="Доступные команды"
    )
    
    # Команда отправки push-уведомления
    send_parser = subparsers.add_parser(
        "send",
        help="Отправить push-уведомление напрямую"
    )
    send_parser.add_argument(
        "--token", "-t",
        required=True,
        help="FCM токен устройства"
    )
    send_parser.add_argument(
        "--title",
        required=True,
        help="Заголовок уведомления"
    )
    send_parser.add_argument(
        "--body", "-b",
        required=True,
        help="Текст уведомления"
    )
    send_parser.add_argument(
        "--data", "-d",
        help="Дополнительные данные в формате JSON"
    )
    send_parser.add_argument(
        "--data-file", "-f",
        help="Файл с дополнительными данными в формате JSON"
    )
    send_parser.add_argument(
        "--topic",
        help="Тема для отправки (если указана, токен игнорируется)"
    )
    send_parser.add_argument(
        "--image", "-i",
        help="URL изображения для уведомления"
    )
    send_parser.add_argument(
        "--badge",
        type=int,
        help="Число для отображения на иконке приложения (iOS)"
    )
    send_parser.add_argument(
        "--click-action",
        help="Действие при клике (URL или deeplink)"
    )
    send_parser.set_defaults(func=send_push)
    
    # Команда обработки webhook
    hook_parser = subparsers.add_parser(
        "hook",
        help="Обработать webhook-запрос"
    )
    hook_parser.add_argument(
        "--hook-data",
        help="Данные webhook в формате JSON"
    )
    hook_parser.add_argument(
        "--hook-file",
        help="Файл с данными webhook в формате JSON"
    )
    hook_parser.set_defaults(func=handle_hook)
    
    # Команда подписки на тему
    subscribe_parser = subparsers.add_parser(
        "subscribe",
        help="Подписать токены на тему"
    )
    subscribe_parser.add_argument(
        "--tokens", "-t",
        required=True,
        help="FCM токены устройств, разделенные запятыми"
    )
    subscribe_parser.add_argument(
        "--topic",
        required=True,
        help="Название темы"
    )
    subscribe_parser.set_defaults(func=subscribe_topic)
    
    # Команда отписки от темы
    unsubscribe_parser = subparsers.add_parser(
        "unsubscribe",
        help="Отписать токены от темы"
    )
    unsubscribe_parser.add_argument(
        "--tokens", "-t",
        required=True,
        help="FCM токены устройств, разделенные запятыми"
    )
    unsubscribe_parser.add_argument(
        "--topic",
        required=True,
        help="Название темы"
    )
    unsubscribe_parser.set_defaults(func=unsubscribe_topic)
    
    # Команда имитации уведомления
    simulate_parser = subparsers.add_parser(
        "simulate",
        help="Имитировать отправку уведомления для тестирования"
    )
    simulate_parser.add_argument(
        "--type", "-y",
        required=True,
        choices=["receive-money", "send-money", "account-activated", "client-status-changed"],
        help="Тип уведомления"
    )
    simulate_parser.add_argument(
        "--token", "-t",
        required=True,
        help="FCM токен устройства"
    )
    simulate_parser.add_argument(
        "--client-id",
        default="test-client-123",
        help="ID клиента"
    )
    simulate_parser.add_argument(
        "--amount",
        type=float,
        help="Сумма (для денежных уведомлений)"
    )
    simulate_parser.add_argument(
        "--currency",
        help="Валюта (для денежных уведомлений)"
    )
    simulate_parser.add_argument(
        "--sender",
        help="Имя отправителя (для receive-money)"
    )
    simulate_parser.add_argument(
        "--recipient",
        help="Имя получателя (для send-money)"
    )
    simulate_parser.add_argument(
        "--account-id",
        help="ID аккаунта"
    )
    simulate_parser.add_argument(
        "--account-type",
        help="Тип аккаунта (для account-activated)"
    )
    simulate_parser.add_argument(
        "--old-status",
        help="Старый статус (для client-status-changed)"
    )
    simulate_parser.add_argument(
        "--new-status",
        help="Новый статус (для client-status-changed)"
    )
    simulate_parser.set_defaults(func=simulate_notification)
    
    # Парсим аргументы
    args = parser.parse_args()
    
    # Если команда не указана, выводим справку
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    # Выполняем функцию для выбранной команды
    return args.func(args)

if __name__ == "__main__":
    import time
    sys.exit(main())