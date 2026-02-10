import os
import sys
import datetime

# Пути и константы
def get_base_path():
    """Возвращает правильный путь к папке с программой"""
    if getattr(sys, 'frozen', False):
        # Если программа запущена как EXE
        base_path = os.path.dirname(sys.executable)
    else:
        # Если программа запущена как скрипт Python
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path

BASE_PATH = get_base_path()
DB_PATH = os.path.join(BASE_PATH, 'Milkman.db')
EXPIRATION_DATE = datetime.date(2027, 1, 1)

# Стили приложения
APP_STYLE = """
QMainWindow {
    background-color: #f5f7fa;
}

QWidget {
    background-color: #f5f7fa;
    color: #333333;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QPushButton {
    background-color: #4a6fa5;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3a5a80;
}

QPushButton:pressed {
    background-color: #2a4a70;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QLineEdit {
    padding: 8px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: white;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #4a6fa5;
}

QLabel {
    color: #333333;
    font-size: 14px;
}

QTableWidget {
    background-color: white;
    border: 1px solid #dddddd;
    border-radius: 4px;
    gridline-color: #e0e0e0;
    selection-background-color: #e6f2ff;
}

QHeaderView::section {
    background-color: #4a6fa5;
    color: white;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QTabWidget::pane {
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: white;
}

QTabBar::tab {
    background-color: #e0e0e0;
    color: #333333;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #4a6fa5;
    color: white;
}

QTabBar::tab:hover:!selected {
    background-color: #d0d0d0;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #cccccc;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 8px;
    background-color: #4a6fa5;
    color: white;
    border-radius: 4px;
}

QDialog {
    background-color: #f5f7fa;
}

QTextEdit {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
    background-color: white;
    font-size: 14px;
}

QComboBox {
    padding: 6px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: white;
    min-height: 20px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    border: 1px solid #cccccc;
    background-color: white;
    selection-background-color: #4a6fa5;
}
"""

# Подразделения по умолчанию
DEFAULT_DEPARTMENTS = [
    (1, "1 отделение"), (2, "2 отделение"), (3, "3 отделение"), (4, "4 отделение"), (5, "5 отделение"),
    (6, "6 отделение"), (7, "7 отделение"), (8, "8 отделение"), (9, "9 отделение"), (10, "10 отделение"),
    (11, "11 отделение"), (12, "12 отделение"), (13, "13 отделение"), (14, "14 отделение"), (15, "15 отделение"),
    (16, "16 отделение"), (17, "17 отделение"), (18, "18 отделение"), (19, "19 отделение"), (20, "20 отделение"),
    (21, "21 отделение"), (22, "22 отделение"), (23, "23 отделение"), (24, "24 отделение"), (25, "25 отделение"),
    (26, "26 отделение"), (27, "27 отделение"), (28, "28 отделение"), (29, "29 отделение"), (30, "30 отделение"),
    (31, "31 отделение"), (32, "32 отделение"), (33, "33 отделение"), (34, "34 отделение"), (35, "35 отделение"),
    (36, "36 отделение"), (37, "37 отделение"), (38, "38 отделение"), (39, "39 отделение"), (40, "40 отделение"),
    (41, "41 отделение"), (42, "42 отделение"), (43, "43 отделение"), (44, "44 отделение"), (45, "45 отделение"),
    (46, "46 отделение"), (47, "47 отделение"), (48, "48 отделение"), (49, "49 отделение"), (50, "50 отделение"),
    (51, "51 отделение"), (52, "52 отделение"), (53, "53 отделение"), (54, "54 отделение"), (55, "55 отделение"),
    (56, "56 отделение"), (57, "57 отделение"), (58, "58 отделение"), (59, "59 отделение"), (60, "60 отделение"),
    (61, "61 отделение"), (62, "62 отделение"), (63, "63 отделение"), (64, "ВП п.Ильинское"), (65, "Приемное отд."),
    (66, "66 отделение"), (67, "Автоотделение"), (68, "Тестовое")
]
REPORTS_DIR = os.path.join(BASE_PATH, 'REZ')  # Папка для отчетов
BASE_REPORTS_DIR = os.path.join(BASE_PATH, 'основа')  # Папка для неизменяемых отчетов