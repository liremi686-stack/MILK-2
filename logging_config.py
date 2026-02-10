import os
import logging
import sys
from datetime import datetime
from config import BASE_PATH

def setup_logging():
    """Настройка системы логирования для всего приложения"""
    
    # Создаем папку для логов если ее нет
    logs_dir = os.path.join(BASE_PATH, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Удаляем существующие обработчики
    root_logger.handlers.clear()
    
    # Обработчик для записи в файл
    log_filename = os.path.join(logs_dir, f'milkman_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Добавляем обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Логируем начало работы
    logging.info("=" * 50)
    logging.info(f"Запуск приложения Milkman - {datetime.now()}")
    logging.info("=" * 50)

def get_module_logger(module_name):
    """Получить логгер для конкретного модуля"""
    return logging.getLogger(module_name)

# Дополнительные утилиты для логирования
def log_exception(logger, exception, message=None):
    """Логирование исключения с дополнительным сообщением"""
    if message:
        logger.error(f"{message}: {exception}")
    else:
        logger.error(f"Исключение: {exception}")
    logger.debug("Трассировка стека:", exc_info=True)

def log_database_error(logger, error, query=None, params=None):
    """Логирование ошибок базы данных"""
    logger.error(f"Ошибка базы данных: {error}")
    if query:
        logger.debug(f"Запрос: {query}")
    if params:
        logger.debug(f"Параметры: {params}")

def log_user_action(logger, user, action, details=None):
    """Логирование действий пользователя"""
    log_message = f"Пользователь {user}: {action}"
    if details:
        log_message += f" - {details}"
    logger.info(log_message)