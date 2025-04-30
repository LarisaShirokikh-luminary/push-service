#!/bin/bash
set -e

# Создаем примеры файлов
python push_cli.py --setup

# Запускаем тесты
pytest -v

# Запускаем интеграционные тесты с CLI
python push_cli.py --all