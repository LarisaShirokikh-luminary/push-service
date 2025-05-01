# Сервис Push-уведомлений с Firebase

Сервис для отправки push-уведомлений через Firebase Cloud Messaging (FCM) с поддержкой Android, iOS и веб-платформ.

## Особенности

- Отправка push-уведомлений на все основные платформы (Android, iOS, Web)
- Обработка различных типов событий (получение денег, отправка денег и т.д.)
- Поддержка скрытых данных в уведомлениях (deep links, идентификаторы)
- Локализация сообщений на разных языках
- Специфические настройки для Android и iOS
- Расширяемая система обработчиков событий

## Установка

### Требования

- Python 3.8 или выше
- Poetry

### Настройка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/LarisaShirokikh-luminary/push-service.git
cd push-service
```

2. Установите зависимости с помощью Poetry:
```bash
poetry install
```

3. Скопируйте пример файла `.env.example` в `.env` и заполните необходимыми значениями:
```bash
cp .env.example .env

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
.
├── .dockerignore
├── .env.example
├── .gitignore
├── credentials
│   └── serviceAccountKey.json
├── docker
│   ├── docker-compose.yml
│   └── Dockerfile
├── firebase-messaging-sw.js
├── index.html
├── logs
├── poetry.lock
├── push_service
│   ├── __init__.py
│   ├── firebase_push.py
│   ├── handlers.py
│   ├── models.py
│   ├── notification_service.py
│   └── web_server.py
├── push_test_app
│   ├── server.py
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   ├── img
│   │   │   └── firebase-logo.png
│   │   ├── js
│   │   │   ├── app.js
│   │   │   └── firebase-init.js
│   │   └── sounds
│   │       └── notification.mp3
│   └── templates
│       ├── index.html
│       └── push_tester.html
├── pyproject.toml
├── README.md
├── serviceAccountKey.json
└── structure.txt

12 directories, 27 files

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

### Запуск веб-приложения

```python
poetry run python push_test_app/server.py
```

### Приложение будет доступно по адресу

```
http://127.0.0.1:8080
```




## Лицензия

MIT