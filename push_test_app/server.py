# push_test_app/server.py
import os
import json
from flask import Flask, request, render_template, jsonify
import logging
from push_service import NotificationService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
notification_service = NotificationService()

@app.route('/')
def index():
    """Главная страница."""
    firebase_config = {
        'firebase_api_key': os.environ.get('FIREBASE_API_KEY', ''),
        'firebase_auth_domain': os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        'firebase_project_id': os.environ.get('FIREBASE_PROJECT_ID', ''),
        'firebase_storage_bucket': os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        'firebase_messaging_sender_id': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        'firebase_app_id': os.environ.get('FIREBASE_APP_ID', ''),
        'firebase_measurement_id': os.environ.get('FIREBASE_MEASUREMENT_ID', ''),
        'firebase_vapid_key': os.environ.get('FIREBASE_VAPID_KEY', '')
    }
    return render_template('index.html', **firebase_config)

@app.route('/api/notifications', methods=['POST'])
def create_notification():
    """Создание и отправка уведомления."""
    data = request.json
    
    title = data.get('title')
    body = data.get('body')
    tokens = data.get('tokens', [])
    additional_data = data.get('data', {})
    
    if not title or not body or not tokens:
        return jsonify({
            'success': False,
            'error': 'Не указаны обязательные параметры (title, body, tokens)'
        }), 400
    
    notification = notification_service.create_notification(
        title=title,
        body=body,
        tokens=tokens,
        data=additional_data
    )
    
    if data.get('send_immediately', True):
        notification = notification_service.send_notification(notification.id)
    
    return jsonify({
        'success': True,
        'notification': notification.to_dict()
    })

@app.route('/api/notifications/<notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Получение информации об уведомлении."""
    notification = notification_service.get_notification(notification_id)
    
    if not notification:
        return jsonify({
            'success': False,
            'error': f'Уведомление с ID {notification_id} не найдено'
        }), 404
    
    return jsonify({
        'success': True,
        'notification': notification.to_dict()
    })

@app.route('/api/notifications/<notification_id>/send', methods=['POST'])
def send_notification(notification_id):
    """Отправка уведомления по ID."""
    try:
        notification = notification_service.send_notification(notification_id)
        return jsonify({
            'success': True,
            'notification': notification.to_dict()
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications', methods=['GET'])
def list_notifications():
    """Получение списка всех уведомлений."""
    notifications = [n.to_dict() for n in notification_service.list_notifications()]
    return jsonify({
        'success': True,
        'notifications': notifications
    })

@app.route('/api/register-token', methods=['POST'])
def register_token():
    """Регистрация FCM токена."""
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Не указан токен'
        }), 400
    
    logging.info(f"Зарегистрирован новый токен: {token}")
    
    return jsonify({
        'success': True,
        'message': 'Токен успешно зарегистрирован'
    })

@app.route('/push-tester')
def push_tester():
    """Страница для тестирования push-уведомлений."""
    firebase_config = {
        'firebase_api_key': os.environ.get('FIREBASE_API_KEY', ''),
        'firebase_auth_domain': os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        'firebase_project_id': os.environ.get('FIREBASE_PROJECT_ID', ''),
        'firebase_storage_bucket': os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        'firebase_messaging_sender_id': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        'firebase_app_id': os.environ.get('FIREBASE_APP_ID', ''),
        'firebase_measurement_id': os.environ.get('FIREBASE_MEASUREMENT_ID', ''),
        'firebase_vapid_key': os.environ.get('FIREBASE_VAPID_KEY', '')
    }
    return render_template('push_tester.html', **firebase_config)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)