"""
Простой веб-сервер для обслуживания файлов для Firebase Messaging.
"""

import os
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Tuple, Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FCMHandler(SimpleHTTPRequestHandler):
    """
    Обработчик HTTP-запросов для Firebase Cloud Messaging.
    Обслуживает файлы Service Worker и другие статические файлы.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def log_message(self, format: str, *args: Any) -> None:
        """Переопределение метода логирования для использования нашего логгера"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self) -> None:
        """Обработка GET-запросов"""
        # Проверка на запрос Service Worker
        if self.path == '/firebase-messaging-sw.js':
            # Проверяем наличие файла
            if os.path.exists('firebase-messaging-sw.js'):
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript')
                self.send_header('Service-Worker-Allowed', '/')
                self.end_headers()
                
                # Отправляем содержимое файла
                with open('firebase-messaging-sw.js', 'rb') as f:
                    self.wfile.write(f.read())
                
                logger.info(f"Отправлен Service Worker: {self.path}")
                return
            else:
                logger.error(f"Файл Service Worker не найден: {self.path}")
                self.send_error(404, "File not found")
                return
        
        # Обработка запроса к корневой директории
        elif self.path == '/' or self.path == '/index.html':
            # Проверяем наличие файла
            if os.path.exists('index.html'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Отправляем содержимое файла
                with open('index.html', 'rb') as f:
                    self.wfile.write(f.read())
                
                logger.info(f"Отправлена главная страница: {self.path}")
                return
        
        # Для всех остальных запросов используем стандартный обработчик
        return super().do_GET()

def run_server(port: int = 8003) -> None:
    """
    Запускает веб-сервер на указанном порту.
    
    Args:
        port: Порт для запуска сервера
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, FCMHandler)
    
    logger.info(f"Запуск веб-сервера на порту {port}")
    logger.info(f"Service Worker будет доступен по адресу: http://localhost:{port}/firebase-messaging-sw.js")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен по запросу пользователя")
    except Exception as e:
        logger.error(f"Ошибка при работе сервера: {e}")
    finally:
        httpd.server_close()
        logger.info("Сервер остановлен")

if __name__ == "__main__":
    # Получаем порт из переменной окружения или используем порт по умолчанию
    port = int(os.environ.get('WEB_SERVER_PORT', 8003))
    run_server(port)