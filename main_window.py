from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database import DatabaseManager
from search_result_window import SearchResultWindow
from utils import CenteredWindow, validate_date
from config import APP_STYLE

class MainWindow(QMainWindow, CenteredWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Milkman Database')
        self.setGeometry(100, 100, 500, 400)
        self.center()
        self.setStyleSheet(APP_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel('База данных Milkman')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # Группа поиска
        search_group = QGroupBox("Поиск и редактирование данных")
        search_layout = QVBoxLayout()
        search_group.setLayout(search_layout)
        
        # Поля ввода
        date_dept_layout = QHBoxLayout()
        
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel('Месяц и год (MM/YYYY или MM.YYYY):'))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText('MM/YYYY или MM.YYYY')
        date_layout.addWidget(self.date_input)
        
        dept_layout = QVBoxLayout()
        dept_layout.addWidget(QLabel('Подразделение:'))
        self.dept_input = QLineEdit()
        self.dept_input.setPlaceholderText('1-68')
        dept_layout.addWidget(self.dept_input)
        
        date_dept_layout.addLayout(date_layout)
        date_dept_layout.addLayout(dept_layout)
        
        search_layout.addLayout(date_dept_layout)
        
        # Кнопка поиска
        self.search_btn = QPushButton('Поиск данных')
        self.search_btn.clicked.connect(self.search_data)
        search_layout.addWidget(self.search_btn)
        
        layout.addWidget(search_group)
        
        # Версия программы
        version_text = 'Версия Revision 1.0'
        version_label = QLabel(version_text)
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #e74c3c; margin-top: 20px; font-weight: bold;")
        layout.addWidget(version_label)
        
        central_widget.setLayout(layout)
    
    def search_data(self):
        date = self.date_input.text()
        dept = self.dept_input.text()
        
        if not validate_date(date):
            QMessageBox.warning(self, 'Ошибка', 'Неверный формат даты! Используйте MM/YYYY или MM.YYYY')
            return
        
        # Проверяем ввод номера подразделения
        if dept:
            if not dept.isdigit():
                QMessageBox.warning(self, 'Ошибка ввода', f'Номер подразделения должен быть числом, а не "{dept}"')
                return
            dept_num = int(dept)
            if not (1 <= dept_num <= 68):
                QMessageBox.warning(self, 'Ошибка', 'Номер подразделения должен быть от 1 до 68')
                return
        else:
            dept_num = None
        
        self.result_window = SearchResultWindow(self.db, date, dept_num)
        self.result_window.showMaximized()