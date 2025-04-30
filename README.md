# Сервис Push-уведомлений с Firebase

Сервис для отправки push-уведомлений через Firebase Cloud Messaging (FCM) с поддержкой Android, iOS и веб-платформ.

## Особенности

- Отправка push-уведомлений на все основные платформы (Android, iOS, Web)
- Обработка различных типов событий (получение денег, отправка денег и т.д.)
- Поддержка скрытых данных в уведомлениях (deep links, идентификаторы)
- Локализация сообщений на разных языках
- Специфические настройки для Android и iOS
- Групповая отправка уведомлений (multicast)
- Поддержка Data-only уведомлений
- Интеграция с Kafka для приема событий
- Расширяемая система обработчиков событий

## Установка

### Требования

- Python 3.8 или выше
- Poetry

### Настройка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/push-notification-service.git
cd push-notification-service
```

2. Установите зависимости с помощью Poetry:
```bash
poetry install
```

3. Скопируйте пример файла `.env.example` в `.env` и заполните необходимыми значениями:
```bash
cp .env.example .env
# Отредактируйте файл .env вашим любимым редактором
```

4. Загрузите файл учетных данных Firebase:
   - Войдите в [Firebase Console](https://console.firebase.google.com/)
   - Перейдите в Настройки проекта > Сервисные аккаунты
   - Создайте новый ключ для Firebase Admin SDK
   - Сохраните полученный JSON файл как `serviceAccountKey.json` в корне проекта

## Использование

### Базовое использование

```python
from push_service import NotificationService

# Инициализация сервиса
service = NotificationService(service_account_path="serviceAccountKey.json")

# Пример данных из Kafka/webhook
event_data = {
    "type": "receive-money",
    "client_id": "12345",
    "amount": "1000.50",
    "currency": "USD",
    "sender": "John Doe",
    "account_id": "ACC123456",
    "transaction_id": "TRX789012"
}

# Отправка уведомления
result = service.handle_hook(event_data)
```

### Интеграция с Kafka

```python
from kafka import KafkaConsumer
from push_service import NotificationService
import json

# Инициализация сервиса
service = NotificationService(service_account_path="serviceAccountKey.json")

# Создание консьюмера Kafka
consumer = KafkaConsumer(
    'notification_events',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Обработка сообщений
for message in consumer:
    try:
        # Отправка уведомления
        result = service.handle_hook(message.value)
        print(f"Notification sent: {result}")
    except Exception as e:
        print(f"Error sending notification: {e}")
```

### Создание пользовательских обработчиков событий

Вы можете создавать свои обработчики для новых типов событий:

```python
from push_service import NotificationService
from push_service.handlers import NotificationHandler

# Создание пользовательского обработчика
class CustomEventHandler(NotificationHandler):
    def process(self, client, data):
        # Обработка события
        event_id = data.get('event_id')
        event_name = data.get('event_name')
        
        # Формирование данных для уведомления
        return {
            'token': client.firebase_token,
            'title': 'Custom Event',
            'body': f'Event {event_name} has occurred',
            'data': {
                'event_id': event_id,
                'action': 'open_event_details',
                'deep_link': f'myapp://events/{event_id}'
            }
        }

# Инициализация сервиса
service = NotificationService(service_account_path="serviceAccountKey.json")

# Регистрация пользовательского обработчика
service.register_handler('custom-event', CustomEventHandler())

# Теперь сервис может обрабатывать события типа 'custom-event'
```

### Отправка групповых уведомлений

```python
from push_service import NotificationService

# Инициализация сервиса
service = NotificationService(service_account_path="serviceAccountKey.json")

# Отправка уведомления группе клиентов
result = service.send_multicast_notification(
    client_ids=["12345", "67890", "54321"],
    title="Maintenance Notification",
    body="Our system will be under maintenance from 2:00 AM to 4:00 AM tomorrow",
    data={
        "type": "maintenance",
        "action": "open_maintenance_details",
        "deep_link": "myapp://maintenance/123"
    }
)

print(f"Sent to {result['success_count']} clients, failed for {result['failure_count']} clients")
```

## Тестирование

### Запуск тестов с помощью pytest

```bash
poetry run pytest
```

### Запуск утилиты CLI для тестирования

```bash
# Создание примеров конфигурационных файлов
python push_cli.py --setup

# Запуск всех тестовых сценариев
python push_cli.py --all

# Отправка конкретного уведомления
python push_cli.py --token YOUR_FCM_TOKEN --message "Test message" --title "Test Title"

# Тестирование определенного типа события
python push_cli.py --webhook-type receive-money --client-id 12345
```

### Запуск через Docker

```bash
# Сборка и запуск контейнера
docker-compose -f docker/docker-compose.yml up --build
```

## Поддерживаемые типы уведомлений

1. **receive-money** - Получение денег
   - Требуемые поля: `amount`, `currency`, `sender`, `account_id`

2. **send-money** - Отправка денег
   - Требуемые поля: `amount`, `currency`, `recipient`, `transaction_id`

3. **account-activated** - Активация аккаунта
   - Требуемые поля: `account_name`, `account_id`

4. **client-status-changed** - Изменение статуса клиента
   - Требуемые поля: `new_status`

## Структура проекта

```
push-notification-service/
├── push_service/              # Основной модуль
│   ├── __init__.py            # Инициализация сервиса
│   ├── models.py              # Модели данных
│   ├── firebase_push.py       # Работа с Firebase
│   └── handlers.py            # Обработчики событий
├── tests/                     # Тесты
│   ├── conftest.py            # Конфигурация тестов
│   └── test_notification_service.py
├── examples/                  # Примеры использования
│   └── kafka_integration.py   # Интеграция с Kafka
├── push_cli.py                # Утилита командной строки
├── pyproject.toml             # Конфигурация Poetry
├── .env.example               # Пример файла окружения
└── README.md                  # Документация
```

## Настройка для клиентских приложений

### Android

```kotlin
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        // Получение данных
        val notification = remoteMessage.notification
        val data = remoteMessage.data
        
        // Обработка deep link
        val deepLink = data["deep_link"]
        if (deepLink != null) {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(deepLink))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            startActivity(intent)
        }
    }
}
```

### iOS (Swift)

```swift
func application(_ application: UIApplication, didReceiveRemoteNotification userInfo: [AnyHashable : Any], fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
    if let data = userInfo["data"] as? [String: Any] {
        let type = data["type"] as? String
        let deepLink = data["deep_link"] as? String
        
        if let deepLink = deepLink, let url = URL(string: deepLink) {
            UIApplication.shared.open(url)
        }
    }
    
    completionHandler(.newData)
}
```

### Web (JavaScript)

```javascript
// Регистрация service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/firebase-messaging-sw.js');
}

// Получение и отображение уведомлений
messaging.onMessage((payload) => {
  const { notification, data } = payload;
  
  // Обработка данных уведомления
  if (data && data.deep_link) {
    // Сохраняем deep link для использования при клике
    localStorage.setItem('last_notification_deep_link', data.deep_link);
  }
  
  // Отображение уведомления
  const notificationTitle = notification.title;
  const notificationOptions = {
    body: notification.body,
    icon: '/path/to/icon.png',
    data: data
  };
  
  new Notification(notificationTitle, notificationOptions);
});
```

## Расширенные возможности

### Персонализация уведомлений

Сервис поддерживает локализацию и персонализацию уведомлений в зависимости от языка и настроек пользователя.

### Data-only сообщения

Для отправки "тихих" уведомлений (без отображения в шторке):

```python
from push_service import FirebasePushService

firebase = FirebasePushService.get_instance("serviceAccountKey.json")

# Отправка Data-only сообщения
firebase.send_push(
    token="user_token",
    title="",  # Не используется для Data-only
    body="",   # Не используется для Data-only
    data={
        "data_only": True,
        "action": "sync_data",
        "sync_id": "12345"
    }
)
```

### Обработка сбоев и повторных отправок

Сервис предоставляет информацию о сбоях при отправке уведомлений, что позволяет реализовать механизм повторных попыток.

## Рекомендации и лучшие практики

1. **Безопасность**: Храните файл `serviceAccountKey.json` в безопасном месте и не включайте его в репозиторий.

2. **Токены устройств**: Регулярно проверяйте и обновляйте токены устройств, так как они могут стать недействительными.

3. **Ограничение размера**: Размер сообщения ограничен 4 КБ, не перегружайте уведомления лишними данными.

4. **Deep Links**: Используйте deep links для улучшения пользовательского опыта, направляя пользователя на нужный экран.

5. **Локализация**: Адаптируйте сообщения под язык пользователя для улучшения взаимодействия.

## Лицензия

MIT