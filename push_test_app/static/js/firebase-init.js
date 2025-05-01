// Инициализация и работа с Firebase Cloud Messaging для клиентской части

// Конфигурация Firebase из проекта push-service-e154f
const firebaseConfig = {
    apiKey: "AIzaSyDNPFZbRyLAOBt1iCZ8xAkL8IC8tMIGj_Y",
    authDomain: "push-service-e154f.firebaseapp.com",
    projectId: "push-service-e154f",
    storageBucket: "push-service-e154f.appspot.com",
    messagingSenderId: "679184734382",
    appId: "1:679184734382:web:8a0bff9c353280fa84f53f",
    measurementId: "G-GNEZ92QK17"
};

// VAPID ключ для веб-приложений
const vapidKey = "BE4FRDRtUA7KeBjkzjDJl0utzugTYqGfdb--VI3dcLX9UWDBLFp1gZK5fhz3sc_CIoyIeYktBiErJwHcnJWjjAs";

// Объект для работы с Firebase
let firebaseApp = null;
let messaging = null;

// Текущий FCM токен
let currentToken = null;

// Функция для инициализации Firebase
async function initializeFirebase() {
    try {
        // Инициализация Firebase
        firebaseApp = firebase.initializeApp(firebaseConfig);
        messaging = firebase.messaging(firebaseApp);

        // Регистрация обработчика сообщений для активного окна
        messaging.onMessage((payload) => {
            console.log('Получено сообщение в активном окне:', payload);

            // Вызываем функцию обработки сообщения, если она определена
            if (typeof handleForegroundMessage === 'function') {
                handleForegroundMessage(payload);
            } else {
                // Иначе просто показываем уведомление через Notification API
                showNotification(payload);
            }
        });

        console.log('Firebase успешно инициализирован');
        return true;
    } catch (error) {
        console.error('Ошибка инициализации Firebase:', error);
        logToUI('error', `Ошибка инициализации Firebase: ${error.message}`);
        return false;
    }
}

// Функция для запроса разрешения и получения токена
async function requestPermissionAndGetToken() {
    try {
        logToUI('info', 'Запрашиваем разрешение на отправку уведомлений...');

        // Запрос разрешения на отправку уведомлений
        const permission = await Notification.requestPermission();

        if (permission !== 'granted') {
            logToUI('error', 'Разрешение на отправку уведомлений не получено!');
            return null;
        }

        logToUI('success', 'Разрешение получено! Получаем FCM токен...');

        // Получение токена
        try {
            currentToken = await messaging.getToken({ vapidKey: vapidKey });

            if (currentToken) {
                console.log('FCM Token:', currentToken);
                logToUI('success', 'FCM токен успешно получен!');
                return currentToken;
            } else {
                logToUI('error', 'Не удалось получить токен. Попробуйте снова.');
                return null;
            }
        } catch (tokenError) {
            console.error('Ошибка получения токена:', tokenError);
            logToUI('error', `Ошибка получения токена: ${tokenError.message}`);
            return null;
        }
    } catch (error) {
        console.error('Ошибка при запросе разрешения:', error);
        logToUI('error', `Ошибка при запросе разрешения: ${error.message}`);
        return null;
    }
}

// Функция для проверки текущего разрешения и получения токена
async function checkPermissionAndGetToken() {
    // Проверяем, поддерживаются ли уведомления
    if (!('Notification' in window)) {
        logToUI('error', 'Этот браузер не поддерживает уведомления');
        return null;
    }

    // Если разрешение уже получено, сразу получаем токен
    if (Notification.permission === 'granted') {
        try {
            currentToken = await messaging.getToken({ vapidKey: vapidKey });

            if (currentToken) {
                console.log('FCM Token (auto):', currentToken);
                logToUI('info', 'FCM токен автоматически получен');
                return currentToken;
            }
        } catch (error) {
            console.error('Ошибка при автоматическом получении токена:', error);
            return null;
        }
    }

    return null;
}

// Функция для показа уведомления в активном окне
function showNotification(payload) {
    // Если нет поддержки Notification API, ничего не делаем
    if (!('Notification' in window)) {
        return;
    }

    // Если нет разрешения, ничего не делаем
    if (Notification.permission !== 'granted') {
        return;
    }

    // Получаем данные уведомления
    const notificationTitle = payload.notification?.title || 'Новое уведомление';
    const notificationOptions = {
        body: payload.notification?.body || 'Получено новое уведомление',
        icon: payload.notification?.image || '/static/img/firebase-logo.png',
        badge: '/static/img/notification-badge.png',
        data: payload.data || {} // Скрытые данные будут здесь
    };

    // Создаем и показываем уведомление
    const notification = new Notification(notificationTitle, notificationOptions);
    console.log('Получено сообщение в активном окне:', payload);

    // Добавим больше информации для диагностики
    console.log('Заголовок:', payload.notification?.title);
    console.log('Текст:', payload.notification?.body);
    console.log('Данные:', payload.data);

    // Обработка клика по уведомлению
    notification.onclick = function () {
        notification.close();

        // Открываем нужную страницу по действию
        const action = payload.data?.action;
        if (action === 'open_profile') {
            window.location.href = '/push-tester';
        } else if (payload.data?.url) {
            window.location.href = payload.data.url;
        }

        window.focus();
    };
}

// Функция для вывода сообщений в UI
function logToUI(type, message) {
    // Проверяем, существует ли элемент для логов
    const logsElement = document.getElementById('logs');
    if (!logsElement) {
        console.log(`[${type}] ${message}`);
        return;
    }

    // Создаем элемент для сообщения
    const logItem = document.createElement('div');
    logItem.className = `log-item log-${type}`;

    // Добавляем временную метку
    const timestamp = new Date().toLocaleTimeString();

    // Формируем содержимое
    logItem.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;

    // Добавляем в элемент логов
    logsElement.appendChild(logItem);

    // Прокручиваем до конца
    logsElement.scrollTop = logsElement.scrollHeight;
}

// Функция для отправки уведомления через API
async function sendPushNotification(data) {
    try {
        logToUI('info', 'Отправка запроса на сервер...');

        // Преобразуем все значения в data в строки
        const stringifiedData = {};
        if (data.data) {
            Object.keys(data.data).forEach(key => {
                stringifiedData[key] = String(data.data[key]);
            });
        }

        // Добавляем изображение в data если оно есть
        if (data.image) {
            stringifiedData['image'] = String(data.image);
        }

        // Добавляем URL для перехода, если он не указан в data
        if (data.url && !stringifiedData['url']) {
            stringifiedData['url'] = String(data.url);
        }

        // Подготавливаем данные для сервера
        const requestData = {
            title: data.title,
            body: data.body,
            tokens: data.token ? [data.token] : [],
            data: stringifiedData
        };

        // Отправляем запрос на правильный эндпоинт
        const response = await fetch('/api/notifications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (response.ok) {
            const notificationId = result.notification && result.notification.id
                ? result.notification.id
                : 'неизвестно';

            logToUI('success', `Уведомление успешно отправлено! ID: ${notificationId}`);
            return result;
        } else {
            logToUI('error', `Ошибка отправки уведомления: ${result.error}`);
            return null;
        }
    } catch (error) {
        console.error('Ошибка отправки запроса:', error);
        logToUI('error', `Ошибка сетевого запроса: ${error.message}`);
        return null;
    }
}

// Экспорт функций
window.FirebaseClient = {
    initializeFirebase,
    requestPermissionAndGetToken,
    checkPermissionAndGetToken,
    sendPushNotification,
    getCurrentToken: () => currentToken
};