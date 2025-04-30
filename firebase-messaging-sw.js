// Firebase Cloud Messaging Service Worker

// Имя и версия кэша
const CACHE_NAME = 'push-notification-cache-v1';

// Firebase App конфигурация (должна совпадать с конфигурацией на странице)
const firebaseConfig = {
    apiKey: "AIzaSyDNPFZbRyLAOBt1iCZ8xAkL8IC8tMIGj_Y",
    authDomain: "push-service-e154f.firebaseapp.com",
    projectId: "push-service-e154f",
    storageBucket: "push-service-e154f.firebasestorage.app",
    messagingSenderId: "679184734382",
    appId: "1:679184734382:web:83a0dfc8347034f084f53f",
    measurementId: "G-2THTKV70Y6"
};

// Импорт Firebase скриптов
importScripts('https://www.gstatic.com/firebasejs/11.6.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/11.6.1/firebase-messaging-compat.js');

// Инициализация Firebase
firebase.initializeApp(firebaseConfig);

// Получение экземпляра Firebase Messaging
const messaging = firebase.messaging();

// Обработка сообщений, полученных в фоновом режиме
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Получено сообщение в фоновом режиме:', payload);

    // Настраиваем уведомление для отображения
    const notificationTitle = payload.notification.title || 'Новое уведомление';
    const notificationOptions = {
        body: payload.notification.body || 'У вас новое сообщение',
        icon: '/path/to/icon.png',
        badge: '/path/to/badge.png',
        data: payload.data, // Передаем дополнительные данные
        // Дополнительные опции уведомления
        vibrate: [100, 50, 100],
        actions: [
            {
                action: 'open',
                title: 'Открыть'
            }
        ]
    };

    // Показываем уведомление
    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Обработка события клика по уведомлению
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Клик по уведомлению', event);

    // Закрываем уведомление
    event.notification.close();

    // Получаем данные из уведомления
    const clickAction = event.notification.data?.click_action || '/';
    const targetScreen = event.notification.data?.target_screen;

    // Открываем нужный URL при клике на уведомление
    // Это позволит приложению обработать переход на соответствующий экран
    const urlToOpen = new URL(clickAction, self.location.origin).href;

    // Этот код пытается найти открытое окно с нашим приложением
    // или открывает новое, и переходит на нужный URL
    const promiseChain = clients.matchAll({
        type: 'window',
        includeUncontrolled: true
    })
        .then((windowClients) => {
            // Пытаемся найти уже открытое окно с нашим приложением
            let windowClient = windowClients.find((windowClient) => {
                return windowClient.url.includes(self.location.origin) && 'focus' in windowClient;
            });

            // Если такое окно найдено, фокусируемся на нем и открываем нужный URL
            if (windowClient) {
                return windowClient.focus().then((focusedClient) => {
                    focusedClient.navigate(urlToOpen);
                });
            }

            // Если такого окна нет, открываем новое
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        });

    event.waitUntil(promiseChain);
});

// Установка Service Worker
self.addEventListener('install', event => {
    console.log('[firebase-messaging-sw.js] Service Worker установлен');
    self.skipWaiting(); // Активируем SW сразу
});

// Активация Service Worker
self.addEventListener('activate', event => {
    console.log('[firebase-messaging-sw.js] Service Worker активирован');
    return self.clients.claim(); // Захватываем контроль над клиентами
});