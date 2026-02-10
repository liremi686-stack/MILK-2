from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

class CenteredWindow:
    def center(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry() if screen else QApplication.desktop().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

def validate_date(date_str):
    """Проверяет корректность формата даты"""
    if not date_str:
        return False
    
    try:
        if '/' in date_str:
            parts = date_str.split('/')
        elif '.' in date_str:
            parts = date_str.split('.')
        else:
            return False
        
        if len(parts) != 2:
            return False
            
        month = int(parts[0])
        year = int(parts[1])
        
        return 1 <= month <= 12 and 2000 <= year <= 2100
    except (ValueError, IndexError):
        return False

def get_month_name(date_str):
    """Возвращает название месяца из строки даты"""
    if not date_str:
        return ""
    
    try:
        if '/' in date_str:
            month_str, _ = date_str.split('/', 1)
        elif '.' in date_str:
            month_str, _ = date_str.split('.', 1)
        else:
            return ""
        
        month = int(month_str)
        month_names = [
            "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return month_names[month] if 1 <= month <= 12 else ""
    except (ValueError, IndexError):
        return ""

def get_progress_color(value):
    """Возвращает цвет прогресс-бара в зависимости от значения"""
    if value < 30:
        return QColor(231, 76, 60)  # Красный
    elif value < 70:
        return QColor(241, 196, 15)  # Желтый
    else:
        return QColor(46, 204, 113)  # Зеленый