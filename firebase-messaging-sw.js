// Импортируем Firebase скрипты
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Конфигурация Firebase
const firebaseConfig = {
    apiKey: "AIzaSyDNPFZbRyLAOBt1iCZ8xAkL8IC8tMIGj_Y",
    authDomain: "push-service-e154f.firebaseapp.com",
    projectId: "push-service-e154f",
    storageBucket: "push-service-e154f.appspot.com",
    messagingSenderId: "679184734382",
    appId: "1:679184734382:web:8a0bff9c353280fa84f53f",
    measurementId: "G-GNEZ92QK17"
};

// Инициализируем Firebase
firebase.initializeApp(firebaseConfig);

// Получаем экземпляр Firebase Messaging
const messaging = firebase.messaging();

// Обработчик фоновых сообщений
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Получено фоновое сообщение', payload);

    // Настройка уведомления
    const notificationTitle = payload.notification.title || 'Новое уведомление';
    const notificationOptions = {
        body: payload.notification.body || '',
        icon: '/static/img/notification-icon.png',
        badge: '/static/img/notification-badge.png', // Опционально
        data: payload.data
    };

    // Показываем уведомление
    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Обработчик клика по уведомлению
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Клик по уведомлению', event);

    // Закрываем уведомление
    event.notification.close();

    // Получаем данные
    const data = event.notification.data || {};
    let targetUrl = '/';

    // Определяем URL для перехода
    // Проверяем наличие прямого URL
    if (data.url) {
        targetUrl = data.url;
    }
    // Проверяем различные типы действий
    else if (data.action) {
        switch (data.action) {
            case 'open_profile':
                targetUrl = '/push-tester';
                break;
            case 'open_account':
                targetUrl = `/accounts/${data.account_id || ''}`;
                break;
            case 'open_transaction':
                targetUrl = `/transactions/${data.transaction_id || ''}`;
                break;
            case 'open_notification':
                targetUrl = `/notifications/${data.notification_id || ''}`;
                break;
        }
    }

    // Открываем окно по указанному URL
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            // Проверяем, есть ли уже открытые окна
            for (let i = 0; i < windowClients.length; i++) {
                const client = windowClients[i];
                if (client.url === targetUrl && 'focus' in client) {
                    return client.focus();
                }
            }

            // Если нет открытых окон, открываем новое
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});