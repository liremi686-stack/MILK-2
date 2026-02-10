from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
                             QMessageBox, QHeaderView, QProgressBar, QMenu, QAction,
                             QColorDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import traceback
import logging

logger = logging.getLogger(__name__)

class ReportsWindow(QWidget):
    def __init__(self, db, date, parent_window):
        super().__init__()
        self.db = db
        self.date = date
        self.parent_window = parent_window
        self.current_reports = []
        self.is_loading = False
        self.initUI()
        QTimer.singleShot(100, self.load_reports)
    
    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Заголовок
        title_label = QLabel('Рапорты')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; padding: 3px;")
        layout.addWidget(title_label)
        
        # Информация о загруженных рапортах
        self.info_label = QLabel('Загружаем рапорты...')
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #666; padding: 2px;")
        layout.addWidget(self.info_label)
        
        # Таблица рапортов
        self.reports_table = QTableWidget()
        self.reports_table.setEditTriggers(self.reports_table.DoubleClicked | self.reports_table.EditKeyPressed)
        self.reports_table.cellChanged.connect(self.on_cell_changed)
        
        # Включаем контекстное меню для таблицы
        self.reports_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reports_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Настройка заголовков таблицы
        headers = ['Номер', 'Отделение'] + [str(i) for i in range(1, 32)]
        self.reports_table.setColumnCount(len(headers))
        self.reports_table.setHorizontalHeaderLabels(headers)
        
        layout.addWidget(self.reports_table, 1)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.add_report_btn = QPushButton('Добавить рапорт')
        self.add_report_btn.clicked.connect(self.add_report)
        self.add_report_btn.setStyleSheet("background-color: #27ae60;")
        button_layout.addWidget(self.add_report_btn)
        
        self.delete_report_btn = QPushButton('Удалить рапорт')
        self.delete_report_btn.clicked.connect(self.delete_report)
        self.delete_report_btn.setStyleSheet("background-color: #e74c3c;")
        button_layout.addWidget(self.delete_report_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Предупреждение
        warning_label = QLabel('ВАЖНО: чтоб увидеть изменения в бд нажмите (Обновить данные), при наличии рапортов сохранение невозможно.')
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 8px; background-color: #ffe6e6; border-radius: 4px; margin-top: 10px;")
        layout.addWidget(warning_label)
        
        self.setLayout(layout)
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для раскраски ячеек рапортов"""
        selected_items = self.reports_table.selectedItems()
        
        if not selected_items:
            return
        
        context_menu = QMenu(self)
        
        # Действие для изменения цвета
        change_color_action = QAction("Изменить цвет выделенных ячеек", self)
        change_color_action.triggered.connect(lambda: self.change_selected_cells_color(selected_items))
        context_menu.addAction(change_color_action)
        
        # Действие для сброса цвета
        reset_color_action = QAction("Сбросить цвет выделенных ячеек", self)
        reset_color_action.triggered.connect(lambda: self.reset_selected_cells_color(selected_items))
        context_menu.addAction(reset_color_action)
        
        context_menu.exec_(self.reports_table.viewport().mapToGlobal(position))
    
    def change_selected_cells_color(self, selected_items):
        """Изменяет цвет выбранных ячеек"""
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                for item in selected_items:
                    # Пропускаем колонки с номером и названием отделения (колонки 0 и 1)
                    if item.column() >= 2:
                        item.setBackground(color)
                        logger.debug(f"Изменен цвет ячейки [{item.row()}, {item.column()}] на {color.name()}")
        except Exception as e:
            logger.error(f"Ошибка при изменении цвета ячеек: {e}")
            QMessageBox.warning(self, 'Ошибка', f'Не удалось изменить цвет: {str(e)}')
    
    def reset_selected_cells_color(self, selected_items):
        """Сбрасывает цвет выбранных ячеек"""
        try:
            for item in selected_items:
                if item.column() >= 2:
                    item.setBackground(QColor(255, 255, 255))
                    logger.debug(f"Сброшен цвет ячейки [{item.row()}, {item.column()}]")
        except Exception as e:
            logger.error(f"Ошибка при сбросе цвета ячеек: {e}")
    
    def load_reports(self):
        try:
            self.is_loading = True
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            month_year = self.date.replace('.', '/')
            reports = self.db.get_all_reports(month_year)
            
            self.progress_bar.setValue(50)
            
            if not reports:
                self.info_label.setText('Нет рапортов для этого месяца')
                self.reports_table.setRowCount(0)
                QTimer.singleShot(100, lambda: self.progress_bar.setVisible(False))
                return
            
            self.current_reports = reports
            self.reports_table.setRowCount(len(reports))
            
            for row_idx, report in enumerate(reports):
                # Номер рапорта
                item = QTableWidgetItem(str(report[1]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.reports_table.setItem(row_idx, 0, item)
                
                # Название отделения
                item = QTableWidgetItem(report[2])
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.reports_table.setItem(row_idx, 1, item)
                
                # Данные по дням (правильная индексация)
                for day in range(1, 32):
                    day_value = report[day + 2]  # Индекс 3 для day1, 4 для day2, ..., 33 для day31
                    if day_value is not None and day_value != '':
                        item = QTableWidgetItem(str(day_value))
                        item.setBackground(QColor(255, 255, 200))  # Желтый фон для изменений
                    else:
                        item = QTableWidgetItem('')
                    self.reports_table.setItem(row_idx, day + 1, item)  # Колонка 2 для day1, 3 для day2, ...
            
            self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.info_label.setText(f'Загружено рапортов: {len(reports)}')
            
            self.progress_bar.setValue(100)
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
            
            logger.info(f"Загружено {len(reports)} рапортов за {month_year}")
            
        except Exception as e:
            self.info_label.setText(f'Ошибка загрузки: {str(e)}')
            logger.error(f"Ошибка при загрузке рапортов: {e}\n{traceback.format_exc()}")
        finally:
            self.is_loading = False
    
    def on_cell_changed(self, row, column):
        if self.is_loading or column < 2:  # Не обрабатываем изменения в номере и названии отдела
            return

        try:
            item = self.reports_table.item(row, column)
            if not item:
                return
    
            report_id = self.current_reports[row][0]
            day = column - 1  # Column 2 -> day1, column 3 -> day2, etc.
        
        # Проверяем, что введено число (если не пустая строка)
            if item.text() and not self.is_float(item.text()):
                QMessageBox.warning(self, 'Ошибка ввода', 
                              f'В ячейке "День {day}" рапорта №{self.current_reports[row][1]} введено нечисловое значение: "{item.text()}"\nПожалуйста, введите число.')
            # Восстанавливаем предыдущее значение
                self.reports_table.blockSignals(True)
                item.setText("")
                self.reports_table.blockSignals(False)
                return
    
        # Получаем department_id из текущего отчета
            cursor = self.db.conn.cursor()
        
        # Извлекаем данные из current_reports (должны содержать department_id)
        # Проверяем структуру данных в current_reports
            if len(self.current_reports[row]) >= 3:
                department_id = self.current_reports[row][2]  # Предполагаем, что department_id в позиции 2
            else:
            # Если структура другая, делаем запрос
                cursor.execute('SELECT department_id FROM reports WHERE id = ?', (report_id,))
                result = cursor.fetchone()
                if not result:
                    QMessageBox.warning(self, 'Ошибка', 'Не найден отчет в базе данных')
                    return
                department_id = result[0]
    
        # Обновляем в базе данных
            self.db.update_report_day(report_id, day, item.text() or '')
    
        # Обновляем данные в родительском окне
            if self.parent_window:
                try:
                    delta = float(item.text()) if item.text() else 0
                    # Вызываем метод обновления данных
                    self.parent_window.update_data_from_report(department_id, day, delta)
                except ValueError:
                    pass
            
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось сохранить изменение: {str(e)}')
            print(traceback.format_exc())
    
    def is_float(self, value):
        """Проверяет, можно ли преобразовать строку в число"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def add_report(self):
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Получаем список отделов для выбора
            departments = self.db.get_departments_list()
            
            if not departments:
                QMessageBox.warning(self, 'Ошибка', 'Нет доступных отделов')
                return
            
            # Показываем диалог выбора отдела
            from PyQt5.QtWidgets import QDialog, QDialogButtonBox
            dialog = QDialog(self)
            dialog.setWindowTitle('Выберите отделение')
            dialog.setModal(True)
            
            layout = QVBoxLayout()
            combo = QComboBox()
            for dept_num, comment in departments:
                combo.addItem(f"{dept_num} - {comment}", dept_num)
            layout.addWidget(combo)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            self.progress_bar.setValue(30)
            
            if dialog.exec_() == QDialog.Accepted:
                dept_num = combo.currentData()
                
                # Проверяем, что номер отдела - число
                if not str(dept_num).isdigit():
                    QMessageBox.warning(self, 'Ошибка ввода', f'Номер отдела должен быть числом, а не "{dept_num}"')
                    return
                
                # Находим department_id по номеру
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT id FROM departments WHERE number = ?', (dept_num,))
                result = cursor.fetchone()
                
                if not result:
                    QMessageBox.warning(self, 'Ошибка', 'Отделение не найдено')
                    return
                
                department_id = result[0]
                month_year = self.date.replace('.', '/')
                
                self.progress_bar.setValue(60)
                
                # Создаем рапорт
                report_number = self.db.create_report(department_id, f"01/{month_year}")
                
                self.progress_bar.setValue(90)
                
                # Обновляем таблицу
                self.load_reports()
                
                self.progress_bar.setValue(100)
                QMessageBox.information(self, 'Успех', f'Рапорт №{report_number} добавлен')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить рапорт: {str(e)}')
            print(traceback.format_exc())
        finally:
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
    
    def delete_report(self):
        try:
            selected_rows = set()
            for item in self.reports_table.selectedItems():
                selected_rows.add(item.row())
            
            if not selected_rows:
                QMessageBox.warning(self, 'Предупреждение', 'Выберите рапорты для удаления')
                return
            
            reply = QMessageBox.question(
                self, 'Подтверждение',
                f'Удалить выбранные рапорты ({len(selected_rows)} шт.)?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.progress_bar.setVisible(True)
                self.progress_bar.setMaximum(len(selected_rows))
                
                for i, row in enumerate(selected_rows):
                    report_id = self.current_reports[row][0]
                    self.db.delete_report(report_id)
                    self.progress_bar.setValue(i + 1)
                
                # Обновляем таблицу
                self.load_reports()
                
                self.progress_bar.setValue(len(selected_rows))
                QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
                
                QMessageBox.information(self, 'Успех', 'Рапорты удалены')
                
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить рапорты: {str(e)}')