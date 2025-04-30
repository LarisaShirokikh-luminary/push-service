# Запуск сервиса Push-уведомлений в Docker

## Подготовка

1. Создайте директорию `credentials` в корне проекта:

```bash
mkdir -p credentials
```

2. Поместите файл учетных данных Firebase `serviceAccountKey.json` в директорию `credentials`:

```bash
mkdir -p credentials
cp /путь/к/вашему/serviceAccountKey.json credentials/serviceAccountKey.json
```

3. Создайте файл `.env` в корне проекта для настройки переменных окружения:

```bash
cp .env.example .env
```

4. Отредактируйте файл `.env`, указав реальные значения:

```
TEST_FCM_TOKEN=your_actual_device_token_here
TEST_FCM_TOKEN_2=another_device_token_here
FIREBASE_CREDENTIALS_PATH=./credentials/serviceAccountKey.json
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_NOTIFICATION_TOPIC=notification_events
```

## Запуск сервиса

### Запуск с Kafka и Zookeeper

Для полноценного запуска сервиса вместе с Kafka и Zookeeper используйте:

```bash
docker-compose -f docker/docker-compose.yml up --build
```

Это запустит:
- Сервис Push-уведомлений
- Zookeeper
- Kafka

Сервис будет выполнять тестовую отправку уведомлений с помощью CLI-утилиты.

### Запуск только тестов

Для запуска только тестов используйте:

```bash
docker-compose -f docker/docker-compose.test.yml up --build
```

Это запустит автоматические тесты и проверит работоспособность сервиса.

## Диагностика

### Проверка логов

Логи контейнера доступны через Docker:

```bash
docker logs push-notification-service
```

Файлы логов также сохраняются в директории `logs/` благодаря настроенному volume.

### Ручное выполнение команд в контейнере

Для запуска команд внутри контейнера используйте:

```bash
docker exec -it push-notification-service bash
```

После этого вы можете вручную запустить тесты или утилиту CLI:

```bash
# Запуск всех тестов
python push_cli.py --all

# Тестирование конкретного события
python push_cli.py --webhook-type receive-money
```