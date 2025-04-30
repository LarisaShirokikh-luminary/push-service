
# tests/conftest.py
import os
from push_service.models import MockClient
import pytest
from typing import Dict

from push_service import NotificationService


class MockDB:
    """Mock database for testing."""
    
    def __init__(self, clients=None):
        self.clients = clients or {}
        self.client = self
    
    def get_by_core_id(self, core_id):
        return self.clients.get(core_id)


@pytest.fixture
def firebase_credentials():
    """Путь к учетным данным Firebase."""
    return os.environ.get('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')


@pytest.fixture
def mock_clients() -> Dict[str, MockClient]:
    """Мок-клиенты для тестирования."""
    return {
        "12345": MockClient(
            core_id="12345",
            firebase_token=os.environ.get("TEST_FCM_TOKEN", "test_token_1"),
            language="en",
        ),
        "67890": MockClient(
            core_id="67890",
            firebase_token=os.environ.get("TEST_FCM_TOKEN_2", "test_token_2"),
            language="ru",
        )
    }


@pytest.fixture
def mock_db(mock_clients):
    """Мок базы данных."""
    return MockDB(mock_clients)


@pytest.fixture
def notification_service(firebase_credentials, mock_db):
    """Экземпляр сервиса уведомлений для тестирования."""
    return NotificationService(
        db=mock_db,
        service_account_path=firebase_credentials
    )


@pytest.fixture
def money_received_hook():
    """Пример данных для уведомления о получении денег."""
    return {
        "type": "receive-money",
        "client_id": "12345",
        "amount": "1000.50",
        "currency": "USD",
        "sender": "John Doe",
        "account_id": "ACC123456",
        "transaction_id": "TRX789012"
    }


@pytest.fixture
def money_sent_hook():
    """Пример данных для уведомления об отправке денег."""
    return {
        "type": "send-money",
        "client_id": "12345",
        "amount": "500.75",
        "currency": "EUR",
        "recipient": "Jane Smith",
        "transaction_id": "TRX654321"
    }


@pytest.fixture
def account_activated_hook():
    """Пример данных для уведомления об активации аккаунта."""
    return {
        "type": "account-activated",
        "client_id": "12345",
        "account_name": "Savings Account",
        "account_id": "ACC987654"
    }


@pytest.fixture
def status_changed_hook():
    """Пример данных для уведомления об изменении статуса."""
    return {
        "type": "client-status-changed",
        "client_id": "12345",
        "new_status": "VIP"
    }