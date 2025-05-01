// Файл: firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/9.6.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.6.1/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: 'ваш_firebase_api_key',
    projectId: 'push-notifications-test',
    messagingSenderId: 'ваш_messaging_sender_id',
    appId: 'ваш_firebase_app_id',
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    console.log('Получено фоновое сообщение:', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/img/firebase-logo.png'
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});