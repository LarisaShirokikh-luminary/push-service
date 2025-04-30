"""
Обработчики различных типов событий для отправки push-уведомлений.
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from .models import Client

# Получение логгера
logger = logging.getLogger("push_service")


class NotificationHandler(ABC):
    """
    Базовый класс для обработчиков уведомлений.
    Определяет интерфейс для всех конкретных обработчиков.
    """
    def __init__(self, db=None):
        """
        Инициализация обработчика
        
        Args:
            db: Объект доступа к базе данных
        """
        self.db = db
    
    @abstractmethod
    def process(self, client: Client, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Абстрактный метод для обработки уведомления
        
        Args:
            client: Объект клиента
            data: Данные события
            
        Returns:
            Словарь с данными для отправки уведомления
        """
        pass
    
    def _format_amount(self, amount, currency):
        """
        Форматирование суммы в зависимости от валюты
        
        Args:
            amount: Сумма (строка или число)
            currency: Код валюты
            
        Returns:
            Отформатированная строка с суммой и символом валюты
        """
        try:
            amount_float = float(amount)
            if currency == 'USD':
                return f"${amount_float:.2f}"
            elif currency == 'EUR':
                return f"€{amount_float:.2f}"
            elif currency == 'RUB':
                return f"{amount_float:.2f} ₽"
            elif currency == 'GBP':
                return f"£{amount_float:.2f}"
            elif currency == 'JPY':
                return f"¥{int(amount_float)}"
            elif currency == 'CNY':
                return f"¥{amount_float:.2f}"
            else:
                return f"{amount_float:.2f} {currency}"
        except (ValueError, TypeError):
            return f"{amount} {currency}"


class MoneyReceivedHandler(NotificationHandler):
    """
    Обработчик уведомлений о получении денег
    """
    def process(self, client: Client, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка события получения денег
        
        Args:
            client: Объект клиента
            data: Данные события
            
        Returns:
            Данные для отправки уведомления
        """
        # Получение необходимых полей
        amount = data.get('amount', '0')
        currency = data.get('currency', 'USD')
        sender = data.get('sender', 'Unknown')
        account_id = data.get('account_id')
        transaction_id = data.get('transaction_id')
        
        # Форматирование суммы
        formatted_amount = self._format_amount(amount, currency)
        
        # Локализация сообщения в зависимости от языка клиента
        language = client.language if hasattr(client, 'language') else 'en'
        
        title, body = self._get_localized_message(language, formatted_amount, sender)
        
        # Специфичные параметры для разных платформ
        android_config = {
            'icon': 'ic_notification_money',
            'color': '#4CAF50',
            'click_action': 'OPEN_ACCOUNT_ACTIVITY'
        }
        
        ios_config = {
            'sound': 'money_received.caf',
            'badge': 1,
            'category': 'TRANSACTION',
            'mutable_content': True
        }
        
        # Дополнительные данные для приложения (не отображаются в уведомлении)
        data_payload = {
            'type': 'receive-money',
            'account_id': account_id,
            'transaction_id': transaction_id,
            'amount': str(amount),
            'currency': currency,
            'action': 'open_account_details',
            'deep_link': f'myapp://accounts/{account_id}/transactions/{transaction_id}'
        }
        
        return {
            'token': client.firebase_token,
            'title': title,
            'body': body,
            'data': data_payload,
            'android': android_config,
            'apns': ios_config
        }
    
    def _get_localized_message(self, language, amount, sender):
        """
        Локализация сообщений в зависимости от языка клиента
        
        Args:
            language: Код языка
            amount: Отформатированная сумма
            sender: Отправитель
            
        Returns:
            Кортеж (заголовок, текст)
        """
        if language == 'ru':
            title = "Поступление средств"
            body = f"Вам поступило {amount} от {sender}"
        elif language == 'es':
            title = "Dinero recibido"
            body = f"Has recibido {amount} de {sender}"
        elif language == 'fr':
            title = "Argent reçu"
            body = f"Vous avez reçu {amount} de {sender}"
        elif language == 'de':
            title = "Geld erhalten"
            body = f"Sie haben {amount} von {sender} erhalten"
        elif language == 'it':
            title = "Denaro ricevuto"
            body = f"Hai ricevuto {amount} da {sender}"
        elif language == 'ja':
            title = "入金通知"
            body = f"{sender}から{amount}を受け取りました"
        elif language == 'zh':
            title = "收款通知"
            body = f"您已收到来自{sender}的{amount}"
        else:  # English by default
            title = "Money Received"
            body = f"You've received {amount} from {sender}"
        
        return title, body


class MoneySentHandler(NotificationHandler):
    """
    Обработчик уведомлений об отправке денег
    """
    def process(self, client: Client, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка события отправки денег
        
        Args:
            client: Объект клиента
            data: Данные события
            
        Returns:
            Данные для отправки уведомления
        """
        # Получение необходимых полей
        amount = data.get('amount', '0')
        currency = data.get('currency', 'USD')
        recipient = data.get('recipient', 'Unknown')
        transaction_id = data.get('transaction_id')
        
        # Форматирование суммы
        formatted_amount = self._format_amount(amount, currency)
        
        # Локализация сообщения в зависимости от языка клиента
        language = client.language if hasattr(client, 'language') else 'en'
        
        title, body = self._get_localized_message(language, formatted_amount, recipient)
        
        # Специфичные параметры для разных платформ
        android_config = {
            'icon': 'ic_notification_money_sent',
            'color': '#2196F3',
            'click_action': 'OPEN_TRANSACTION_ACTIVITY'
        }
        
        ios_config = {
            'sound': 'money_sent.caf',
            'badge': 1,
            'category': 'TRANSACTION',
            'mutable_content': True
        }
        
        # Дополнительные данные для приложения
        data_payload = {
            'type': 'send-money',
            'transaction_id': transaction_id,
            'amount': str(amount),
            'currency': currency,
            'recipient': recipient,
            'action': 'open_transaction_details',
            'deep_link': f'myapp://transactions/{transaction_id}'
        }
        
        return {
            'token': client.firebase_token,
            'title': title,
            'body': body,
            'data': data_payload,
            'android': android_config,
            'apns': ios_config
        }
    
    def _get_localized_message(self, language, amount, recipient):
        """
        Локализация сообщений в зависимости от языка клиента
        
        Args:
            language: Код языка
            amount: Отформатированная сумма
            recipient: Получатель
            
        Returns:
            Кортеж (заголовок, текст)
        """
        if language == 'ru':
            title = "Перевод выполнен"
            body = f"Вы отправили {amount} получателю {recipient}"
        elif language == 'es':
            title = "Transferencia completada"
            body = f"Has enviado {amount} a {recipient}"
        elif language == 'fr':
            title = "Transfert effectué"
            body = f"Vous avez envoyé {amount} à {recipient}"
        elif language == 'de':
            title = "Überweisung abgeschlossen"
            body = f"Sie haben {amount} an {recipient} gesendet"
        elif language == 'it':
            title = "Trasferimento completato"
            body = f"Hai inviato {amount} a {recipient}"
        elif language == 'ja':
            title = "送金完了"
            body = f"{recipient}に{amount}を送金しました"
        elif language == 'zh':
            title = "转账完成"
            body = f"您已向{recipient}发送{amount}"
        else:  # English by default
            title = "Transfer Completed"
            body = f"You sent {amount} to {recipient}"
        
        return title, body


class AccountActivatedHandler(NotificationHandler):
    """
    Обработчик уведомлений об активации аккаунта
    """
    def process(self, client: Client, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка события активации аккаунта
        
        Args:
            client: Объект клиента
            data: Данные события
            
        Returns:
            Данные для отправки уведомления
        """
        # Получение необходимых полей
        account_name = data.get('account_name', 'Your account')
        account_id = data.get('account_id')
        
        # Локализация сообщения в зависимости от языка клиента
        language = client.language if hasattr(client, 'language') else 'en'
        
        title, body = self._get_localized_message(language, account_name)
        
        # Специфичные параметры для разных платформ
        android_config = {
            'icon': 'ic_notification_account',
            'color': '#4CAF50',
            'click_action': 'OPEN_ACCOUNT_ACTIVITY'
        }
        
        ios_config = {
            'sound': 'account_activated.caf',
            'badge': 1,
            'category': 'ACCOUNT',
            'mutable_content': True
        }
        
        # Дополнительные данные для приложения
        data_payload = {
            'type': 'account-activated',
            'account_id': account_id,
            'account_name': account_name,
            'action': 'open_account_details',
            'deep_link': f'myapp://accounts/{account_id}'
        }
        
        return {
            'token': client.firebase_token,
            'title': title,
            'body': body,
            'data': data_payload,
            'android': android_config,
            'apns': ios_config
        }
    
    def _get_localized_message(self, language, account_name):
        """
        Локализация сообщений в зависимости от языка клиента
        
        Args:
            language: Код языка
            account_name: Название аккаунта
            
        Returns:
            Кортеж (заголовок, текст)
        """
        if language == 'ru':
            title = "Аккаунт активирован"
            body = f"Счет «{account_name}» успешно активирован"
        elif language == 'es':
            title = "Cuenta activada"
            body = f"La cuenta {account_name} ha sido activada exitosamente"
        elif language == 'fr':
            title = "Compte activé"
            body = f"Le compte {account_name} a été activé avec succès"
        elif language == 'de':
            title = "Konto aktiviert"
            body = f"Das Konto {account_name} wurde erfolgreich aktiviert"
        elif language == 'it':
            title = "Account attivato"
            body = f"L'account {account_name} è stato attivato con successo"
        elif language == 'ja':
            title = "アカウント有効化完了"
            body = f"{account_name}が正常に有効化されました"
        elif language == 'zh':
            title = "账户已激活"
            body = f"{account_name}已成功激活"
        else:  # English by default
            title = "Account Activated"
            body = f"{account_name} has been successfully activated"
        
        return title, body


class StatusChangedHandler(NotificationHandler):
    """
    Обработчик уведомлений об изменении статуса клиента
    """
    def process(self, client: Client, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка события изменения статуса клиента
        
        Args:
            client: Объект клиента
            data: Данные события
            
        Returns:
            Данные для отправки уведомления
        """
        # Получение необходимых полей
        new_status = data.get('new_status', '')
        
        # Локализация сообщения в зависимости от языка клиента
        language = client.language if hasattr(client, 'language') else 'en'
        
        title, body = self._get_localized_message(language, new_status)
        
        # Специфичные параметры для разных платформ
        android_config = {
            'icon': 'ic_notification_status',
            'color': '#FFC107',
            'click_action': 'OPEN_PROFILE_ACTIVITY'
        }
        
        ios_config = {
            'sound': 'status_changed.caf',
            'badge': 1,
            'category': 'PROFILE',
            'mutable_content': True
        }
        
        # Дополнительные данные для приложения
        data_payload = {
            'type': 'client-status-changed',
            'new_status': new_status,
            'action': 'open_profile',
            'deep_link': 'myapp://profile'
        }
        
        return {
            'token': client.firebase_token,
            'title': title,
            'body': body,
            'data': data_payload,
            'android': android_config,
            'apns': ios_config
        }
    
    def _get_localized_message(self, language, status):
        """
        Локализация сообщений в зависимости от языка клиента
        
        Args:
            language: Код языка
            status: Новый статус
            
        Returns:
            Кортеж (заголовок, текст)
        """
        # Локализация специальных статусов
        localized_status = self._localize_status(language, status)
        
        if language == 'ru':
            title = "Изменение статуса"
            body = f"Ваш статус обновлен до «{localized_status}»"
        elif language == 'es':
            title = "Cambio de estado"
            body = f"Tu estado ha sido actualizado a {localized_status}"
        elif language == 'fr':
            title = "Changement de statut"
            body = f"Votre statut a été mis à jour vers {localized_status}"
        elif language == 'de':
            title = "Statusänderung"
            body = f"Ihr Status wurde auf {localized_status} aktualisiert"
        elif language == 'it':
            title = "Cambio di stato"
            body = f"Il tuo stato è stato aggiornato a {localized_status}"
        elif language == 'ja':
            title = "ステータス変更"
            body = f"ステータスが{localized_status}に更新されました"
        elif language == 'zh':
            title = "状态更改"
            body = f"您的状态已更新为{localized_status}"
        else:  # English by default
            title = "Status Updated"
            body = f"Your status has been updated to {localized_status}"
        
        return title, body
    
    def _localize_status(self, language, status):
        """
        Локализация статусов
        
        Args:
            language: Код языка
            status: Статус
            
        Returns:
            Локализованное название статуса
        """
        statuses = {
            'VIP': {
                'ru': 'ВИП',
                'es': 'VIP',
                'fr': 'VIP',
                'de': 'VIP',
                'it': 'VIP',
                'ja': 'VIP',
                'zh': 'VIP',
                'en': 'VIP'
            },
            'PREMIUM': {
                'ru': 'Премиум',
                'es': 'Premium',
                'fr': 'Premium',
                'de': 'Premium',
                'it': 'Premium',
                'ja': 'プレミアム',
                'zh': '高级会员',
                'en': 'Premium'
            },
            'STANDARD': {
                'ru': 'Стандарт',
                'es': 'Estándar',
                'fr': 'Standard',
                'de': 'Standard',
                'it': 'Standard',
                'ja': 'スタンダード',
                'zh': '标准',
                'en': 'Standard'
            },
            'BASIC': {
                'ru': 'Базовый',
                'es': 'Básico',
                'fr': 'Basique',
                'de': 'Basis',
                'it': 'Base',
                'ja': 'ベーシック',
                'zh': '基本',
                'en': 'Basic'
            }
        }
        
        if status.upper() in statuses:
            return statuses[status.upper()].get(language, statuses[status.upper()]['en'])
        
        return status