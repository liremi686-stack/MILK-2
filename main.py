import sys
from PyQt5.QtWidgets import QApplication
from security import check_and_self_destruct
from main_window import MainWindow
from config import APP_STYLE
import logging
from logging_config import setup_logging  # Импортируем настройку логирования

def initialize_database():
    """Инициализация базы данных при первом запуске"""
    import os
    from config import DB_PATH
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Если базы данных нет в папке с EXE, создаем новую
    if not os.path.exists(DB_PATH):
        logger.info("Создание новой базы данных...")
        try:
            # Можно скопировать шаблон базы данных из ресурсов
            # или создать новую через DatabaseManager
            from database import DatabaseManager
            db = DatabaseManager()
            logger.info("База данных создана успешно")
        except Exception as e:
            logger.error(f"Ошибка при создании базы данных: {e}")
            raise

if __name__ == '__main__':
    # Настройка логирования перед всеми действиями
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Проверка даты перед запуском
        logger.info("Проверка срока действия программы...")
        check_and_self_destruct()
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        app.setStyleSheet(APP_STYLE)
        
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Приложение успешно запущено")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
        sys.exit(1)