"""
Тесты для сервиса уведомлений.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from push_service import NotificationService, FirebasePushService, PushError
from push_service.models import Client, MockClient


class TestNotificationService:
    """
    Тесты для основного сервиса уведомлений.
    """
    
    @pytest.fixture
    def mock_db(self):
        """Мок базы данных с тестовыми клиентами."""
        clients = {
            "12345": MockClient(
                core_id="12345",
                firebase_token="test_token_1",
                language="en",
            ),
            "67890": MockClient(
                core_id="67890",
                firebase_token="test_token_2",
                language="ru",
            ),
            "no_token": MockClient(
                core_id="no_token",
                firebase_token=None,
                language="en",
            ),
            "disabled": MockClient(
                core_id="disabled",
                firebase_token="test_token_3",
                language="en",
            )
        }
        
        # Отключаем уведомления для клиента "disabled"
        clients["disabled"].notification_settings = {"enabled": False}
        
        mock_db = MagicMock()
        mock_db.client.get_by_core_id = lambda core_id: clients.get(core_id)
        
        return mock_db
    
    @pytest.fixture
    def service(self, mock_db):
        """Экземпляр сервиса уведомлений с замоканной Firebase."""
        with patch.object(FirebasePushService, 'get_instance') as mock_firebase:
            # Настраиваем мок для send_push метода
            mock_instance = MagicMock()
            mock_instance.send_push.return_value = "message_id_123"
            mock_instance.send_multicast.return_value = {
                "success_count": 2,
                "failure_count": 0,
                "message_ids": ["id1", "id2"],
                "failed_tokens": []
            }
            mock_firebase.return_value = mock_instance
            
            service = NotificationService(db=mock_db)
            yield service
    
    def test_handle_hook_money_received(self, service):
        """Тест обработки события получения денег."""
        event_data = {
            "type": "receive-money",
            "client_id": "12345",
            "amount": "1000.50",
            "currency": "USD",
            "sender": "John Doe",
            "account_id": "ACC123456",
            "transaction_id": "TRX789012"
        }
        
        result = service.handle_hook(event_data)
        
        assert result == "message_id_123"
        # Проверяем, что метод отправки был вызван с правильными аргументами
        service.firebase.send_push.assert_called_once()
        call_args = service.firebase.send_push.call_args[1]
        
        assert call_args["token"] == "test_token_1"
        assert call_args["title"] == "Money Received"
        assert "You've received" in call_args["body"]
        assert "$1000.50" in call_args["body"]
        assert call_args["data"]["account_id"] == "ACC123456"
        assert call_args["data"]["transaction_id"] == "TRX789012"
    
    def test_handle_hook_money_received_ru(self, service):
        """Тест обработки события получения денег для русскоязычного клиента."""
        event_data = {
            "type": "receive-money",
            "client_id": "67890",
            "amount": "5000",
            "currency": "RUB",
            "sender": "Иван Петров",
            "account_id": "ACC555666",
            "transaction_id": "TRX111222"
        }
        
        result = service.handle_hook(event_data)
        
        assert result == "message_id_123"
        # Проверяем, что метод отправки был вызван с правильными аргументами
        service.firebase.send_push.assert_called_once()
        call_args = service.firebase.send_push.call_args[1]
        
        assert call_args["token"] == "test_token_2"
        assert call_args["title"] == "Поступление средств"
        assert "Вам поступило" in call_args["body"]
        assert "5000.00 ₽" in call_args["body"]
        assert call_args["data"]["account_id"] == "ACC555666"
        assert call_args["data"]["transaction_id"] == "TRX111222"
    
    def test_handle_hook_send_money(self, service):
        """Тест обработки события отправки денег."""
        event_data = {
            "type": "send-money",
            "client_id": "12345",
            "amount": "500.75",
            "currency": "EUR",
            "recipient": "Jane Smith",
            "transaction_id": "TRX654321"
        }
        
        result = service.handle_hook(event_data)
        
        assert result == "message_id_123"
        service.firebase.send_push.assert_called_once()
        call_args = service.firebase.send_push.call_args[1]
        
        assert call_args["token"] == "test_token_1"
        assert call_args["title"] == "Transfer Completed"
        assert "You sent" in call_args["body"]
        assert "€500.75" in call_args["body"]
        assert call_args["data"]["transaction_id"] == "TRX654321"
    
    def test_handle_hook_account_activated(self, service):
        """Тест обработки события активации аккаунта."""
        event_data = {
            "type": "account-activated",
            "client_id": "12345",
            "account_name": "Savings Account",
            "account_id": "ACC987654"
        }
        
        result = service.handle_hook(event_data)
        
        assert result == "message_id_123"
        service.firebase.send_push.assert_called_once()
        call_args = service.firebase.send_push.call_args[1]
        
        assert call_args["token"] == "test_token_1"
        assert call_args["title"] == "Account Activated"
        assert "Savings Account" in call_args["body"]
        assert call_args["data"]["account_id"] == "ACC987654"
    
    def test_handle_hook_client_status_changed(self, service):
        """Тест обработки события изменения статуса."""
        event_data = {
            "type": "client-status-changed",
            "client_id": "12345",
            "new_status": "VIP"
        }
        
        result = service.handle_hook(event_data)
        
        assert result == "message_id_123"
        service.firebase.send_push.assert_called_once()
        call_args = service.firebase.send_push.call_args[1]
        
        assert call_args["token"] == "test_token_1"
        assert call_args["title"] == "Status Updated"
        assert "Your status has been updated to VIP" in call_args["body"]
        assert call_args["data"]["new_status"] == "VIP"
    
    def test_handle_hook_no_client(self, service):
        """Тест обработки события с несуществующим клиентом."""
        event_data = {
            "type": "receive-money",
            "client_id": "99999",
            "amount": "100",
            "currency": "USD"
        }
        
        result = service.handle_hook(event_data)
        
        assert result is None
        service.firebase.send_push.assert_not_called()
    
    def test_handle_hook_invalid_event_type(self, service):
        """Тест обработки события с неизвестным типом."""
        event_data = {
            "type": "unknown-type",
            "client_id": "12345"
        }
        
        result = service.handle_hook(event_data)
        
        assert result is None
        service.firebase.send_push.assert_not_called()
    
    def test_handle_hook_no_token(self, service):
        """Тест обработки события для клиента без токена."""
        event_data = {
            "type": "receive-money",
            "client_id": "no_token",
            "amount": "100",
            "currency": "USD"
        }
        
        result = service.handle_hook(event_data)
        
        assert result is None
        service.firebase.send_push.assert_not_called()
    
    def test_handle_hook_notifications_disabled(self, service):
        """Тест обработки события для клиента с отключенными уведомлениями."""
        event_data = {
            "type": "receive-money",
            "client_id": "disabled",
            "amount": "100",
            "currency": "USD"
        }
        
        result = service.handle_hook(event_data)
        
        assert result is None
        service.firebase.send_push.assert_not_called()
    
    def test_send_multicast_notification(self, service):
        """Тест групповой отправки уведомлений."""
        result = service.send_multicast_notification(
            client_ids=["12345", "67890"],
            title="Test Title",
            body="Test Body",
            data={"key": "value"}
        )
        
        assert result["success_count"] == 2
        assert result["failure_count"] == 0
        assert len(result["message_ids"]) == 2
        
        service.firebase.send_multicast.assert_called_once()
        call_args = service.firebase.send_multicast.call_args[1]
        
        # Проверяем, что в списке токенов только один валидный токен
        assert len(call_args["tokens"]) == 1
        assert call_args["tokens"][0] == "test_token_1"
        
    def test_register_custom_handler(self, service):
        """Тест регистрации пользовательского обработчика."""
        from push_service.handlers import NotificationHandler
        
        # Создаем пользовательский обработчик
        class CustomHandler(NotificationHandler):
            def process(self, client, data):
                return {
                    'token': client.firebase_token,
                    'title': 'Custom Title',
                    'body': 'Custom Body',
                    'data': {'custom_key': 'custom_value'}
                }
        
        # Регистрируем пользовательский обработчик
        custom_handler = CustomHandler()
        service.register_handler('custom-event', custom_handler)
        
        # Проверяем, что обработчик добавлен
        assert 'custom-event' in service.handlers
        
        # Тестируем обработку события с пользовательским обработчиком
        event_data = {
            'type': 'custom-event',
            'client_id': '12345'
        }
        
        result = service.handle_hook(event_data)
        
        assert result == "message_id_123"
        service.firebase.send_push.assert_called_once()
        call_args = service.firebase.send_push.call_args[1]
        
        assert call_args["token"] == "test_token_1"
        assert call_args["title"] == "Custom Title"
        assert call_args["body"] == "Custom Body"
        assert call_args["data"] == {'custom_key': 'custom_value'}
        
        assert set(call_args["tokens"]) == {"test_token_1", "test_token_2"}
        assert call_args["title"] == "Test Title"
        assert call_args["body"] == "Test Body"
        assert call_args["data"] == {"key": "value"}
    
    def test_send_multicast_notification_some_invalid(self, service):
        """Тест групповой отправки уведомлений с невалидными клиентами."""
        result = service.send_multicast_notification(
            client_ids=["12345", "no_token", "disabled", "99999"],
            title="Test Title",
            body="Test Body"
        )
        
        assert result["success_count"] == 2
        assert result["failure_count"] == 0
        
        service.firebase.send_multicast.assert_called_once()
        call_args = service.firebase.send_multicast.call_args[1]