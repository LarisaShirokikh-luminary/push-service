// Основной скрипт для тестового веб-приложения

// Функция для инициализации приложения
async function initApp() {
    // Инициализация Firebase
    if (await window.FirebaseClient.initializeFirebase()) {
        console.log('Firebase инициализирован');

        // Проверяем, есть ли уже разрешение и токен
        const token = await window.FirebaseClient.checkPermissionAndGetToken();
        if (token) {
            updateTokenUI(token);
        }
    } else {
        console.error('Ошибка инициализации Firebase');
    }

    // Привязка обработчиков событий
    setupEventHandlers();
}

// Функция для привязки обработчиков событий
function setupEventHandlers() {
    // Кнопка запроса разрешения и получения токена
    const requestPermissionBtn = document.getElementById('requestPermission');
    if (requestPermissionBtn) {
        requestPermissionBtn.addEventListener('click', async () => {
            const token = await window.FirebaseClient.requestPermissionAndGetToken();
            if (token) {
                updateTokenUI(token);
            }
        });
    }

    // Кнопка копирования токена
    const copyTokenBtn = document.getElementById('copyToken');
    if (copyTokenBtn) {
        copyTokenBtn.addEventListener('click', () => {
            copyTokenToClipboard();
        });
    }

    // Форма отправки уведомления
    const pushForm = document.getElementById('pushForm');
    if (pushForm) {
        pushForm.addEventListener('submit', (event) => {
            event.preventDefault();
            handlePushFormSubmit();
        });
    }

    // Переключатель использования темы
    const useTopicCheckbox = document.getElementById('useTopic');
    if (useTopicCheckbox) {
        useTopicCheckbox.addEventListener('change', function () {
            const topicGroup = document.getElementById('topicGroup');
            if (topicGroup) {
                topicGroup.style.display = this.checked ? 'block' : 'none';
            }
        });
    }

    // Кнопка очистки логов
    const clearLogsBtn = document.getElementById('clearLogs');
    if (clearLogsBtn) {
        clearLogsBtn.addEventListener('click', () => {
            const logsElement = document.getElementById('logs');
            if (logsElement) {
                logsElement.innerHTML = '';
                addLog('info', 'Логи очищены');
            }
        });
    }
}

// Функция для обновления UI с токеном
function updateTokenUI(token) {
    const tokenElement = document.getElementById('fcmToken');
    const tokenStatus = document.getElementById('tokenStatus');
    const copyButton = document.getElementById('copyToken');
    const tokenInput = document.getElementById('token');

    if (tokenElement) {
        tokenElement.textContent = token;
        tokenElement.style.display = 'block';
    }

    if (tokenStatus) {
        tokenStatus.innerHTML = '<strong>✅ FCM токен успешно получен!</strong>';
        tokenStatus.className = 'alert alert-success';
    }

    if (copyButton) {
        copyButton.style.display = 'inline-block';
    }

    // Заполняем поле токена в форме, если оно есть
    if (tokenInput) {
        tokenInput.value = token;
    }
}

// Функция для копирования токена в буфер обмена
function copyTokenToClipboard() {
    const token = window.FirebaseClient.getCurrentToken();

    if (!token) {
        addLog('error', 'Нет токена для копирования');
        return;
    }

    navigator.clipboard.writeText(token)
        .then(() => {
            addLog('success', 'Токен скопирован в буфер обмена');
        })
        .catch(err => {
            addLog('error', `Не удалось скопировать токен: ${err.message}`);
        });
}

// Функция для добавления логов
function addLog(type, message) {
    const logsElement = document.getElementById('logs');
    if (!logsElement) return;

    const logItem = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString();

    // Определяем класс в зависимости от типа сообщения
    let className = '';
    switch (type) {
        case 'success':
            className = 'text-success';
            break;
        case 'error':
            className = 'text-danger';
            break;
        case 'warning':
            className = 'text-warning';
            break;
        default:
            className = 'text-info';
    }

    logItem.className = className;
    logItem.innerHTML = `[${timestamp}] ${message}`;

    logsElement.appendChild(logItem);
    logsElement.scrollTop = logsElement.scrollHeight;
}

// Обработчик для приема уведомлений в активном окне
function handleForegroundMessage(payload) {
    console.log('Обработка сообщения в активном окне:', payload);

    // Добавляем лог о получении сообщения
    addLog('success', `Получено уведомление: ${payload.notification?.title} - ${payload.notification?.body}`);

    // Показываем уведомление через Notification API
    if ('Notification' in window && Notification.permission === 'granted') {
        const notificationTitle = payload.notification?.title || 'Новое уведомление';
        const notificationOptions = {
            body: payload.notification?.body || 'Получено новое уведомление',
            icon: payload.notification?.image || '/static/img/firebase-logo.png',
            data: payload.data || {}
        };

        new Notification(notificationTitle, notificationOptions);
    }

    // Воспроизводим звуковое уведомление
    playNotificationSound();
}

// Функция воспроизведения звука уведомления
function playNotificationSound() {
    try {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.5;
        audio.play();
    } catch (error) {
        console.error('Ошибка воспроизведения звука:', error);
    }
}

// Обработчик отправки формы push-уведомления
async function handlePushFormSubmit() {
    // Получаем значения полей формы
    const token = document.getElementById('token').value || window.FirebaseClient.getCurrentToken();
    const title = document.getElementById('title').value;
    const body = document.getElementById('body').value;
    const dataText = document.getElementById('data').value;
    const image = document.getElementById('image').value;
    const useTopic = document.getElementById('useTopic').checked;
    const topic = document.getElementById('topic').value;

    // Проверка обязательных полей
    if (!title) {
        addLog('error', 'Не указан заголовок уведомления');
        return;
    }

    if (!body) {
        addLog('error', 'Не указан текст уведомления');
        return;
    }

    if (!useTopic && !token) {
        addLog('error', 'Необходимо указать FCM токен или выбрать отправку на тему');
        return;
    }

    if (useTopic && !topic) {
        addLog('error', 'Не указано название темы');
        return;
    }

    // Парсим JSON дополнительных данных
    let data = {};
    if (dataText) {
        try {
            data = JSON.parse(dataText);
        } catch (error) {
            addLog('error', `Ошибка в формате JSON данных: ${error.message}`);
            return;
        }
    }

    // Формируем данные для отправки
    const requestData = {
        title: title,
        body: body,
        data: data
    };

    // Добавляем URL изображения, если указан
    if (image) {
        requestData.image = image;
    }

    // Добавляем получателя (токен или тему)
    if (useTopic) {
        requestData.topic = topic;
    } else {
        requestData.token = token;
    }

    // Отправляем запрос
    addLog('info', 'Отправка запроса на сервер...');

    const result = await window.FirebaseClient.sendPushNotification(requestData);

    if (result) {
        addLog('success', `Уведомление успешно отправлено! ID: ${result.message_id}`);
    }
}

// Загрузка приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', initApp);