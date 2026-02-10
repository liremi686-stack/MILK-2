from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
                             QSplitter, QMenu, QAction, QColorDialog, QProgressBar, QProgressDialog
                             )
from PyQt5.QtCore import Qt, QSettings, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from reports_window import ReportsWindow
from utils import get_month_name
from config import APP_STYLE
from old_report_generator import OldReportGenerator
import logging

logger = logging.getLogger(__name__)

# Класс для фоновой обработки
class WorkerThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, task_type, *args):
        super().__init__()
        self.task_type = task_type
        self.args = args
    
    def run(self):
        try:
            if self.task_type == 'save_data':
                self.save_data_worker()
            elif self.task_type == 'load_data':
                self.load_data_worker()
            elif self.task_type == 'generate_report':
                self.generate_report_worker()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def save_data_worker(self):
        # Имитация долгой операции сохранения
        for i in range(100):
            self.progress.emit(i)
            self.msleep(10)  # Небольшая задержка
    
    def load_data_worker(self):
        # Имитация долгой операции загрузки
        for i in range(100):
            self.progress.emit(i)
            self.msleep(5)
    
    def generate_report_worker(self):
        # Имитация долгой операции генерации отчета
        for i in range(100):
            self.progress.emit(i)
            self.msleep(20)

class SearchResultWindow(QWidget):
    def __init__(self, db, date, department_num):
        super().__init__()
        self.db = db
        self.date = date
        self.department_num = department_num
        self.reports_window = None
        self.dept_id_to_row = {}
        self.is_loading_data = False
        self.pending_recalculations = set()
        self.recalculate_timer = QTimer()
        self.recalculate_timer.setSingleShot(True)
        self.worker_thread = None
        
        # Инициализация UI перед подключением таймера
        self.initUI()
        
        # Теперь подключаем таймер после того как метод recalculate_pending_rows определен
        self.recalculate_timer.timeout.connect(self.recalculate_pending_rows)
        
        QTimer.singleShot(100, self.load_data)

    def _check_reports_warning(self, report_type="отчет"):
        """Универсальная проверка наличия рапортов с предупреждением"""
        month_year = self.date.replace('.', '/')
        reports_exist = self.db.check_reports_exist(month_year)
        
        if not reports_exist:
            return True  # Продолжать без предупреждения
        
        cursor = self.db.conn.cursor()
        changed_departments = []
        departments = cursor.execute(
            'SELECT id, number, comment FROM departments ORDER BY number'
        ).fetchall()
        
        for dept_id, dept_num, comment in departments:
            reports_data = cursor.execute('''
                SELECT day1, day2, day3, day4, day5, day6, day7, day8, day9, day10,
                       day11, day12, day13, day14, day15, day16, day17, day18, day19, day20,
                       day21, day22, day23, day24, day25, day26, day27, day28, day29, day30, day31
                FROM reports 
                WHERE department_id = ? AND date LIKE ?
            ''', (dept_id, f'%/{month_year}')).fetchall()
            
            has_changes = False
            total_change = 0
            
            for report in reports_data:
                for day_idx in range(31):
                    delta_str = report[day_idx]
                    if delta_str and delta_str.strip():
                        try:
                            delta = float(delta_str)
                            if delta != 0:
                                has_changes = True
                                total_change += delta
                        except ValueError:
                            pass
            
            if has_changes:
                changed_departments.append({
                    'number': dept_num,
                    'comment': comment,
                    'total_change': total_change
                })
        
        if changed_departments:
            message = (f'ВНИМАНИЕ: В выбранном месяце имеются рапорты, '
                      f'которые изменяют исходные данные.\n\n'
                      f'{report_type.capitalize()} будет создан с учетом изменений из рапортов.\n\n'
                      f'Количество отделов с изменениями: {len(changed_departments)}\n\n')
            
            max_to_show = 5
            for i, dept in enumerate(changed_departments[:max_to_show]):
                message += f'  • Отдел {dept["number"]} ({dept["comment"]}): изменение {dept["total_change"]:.1f}\n'
            
            if len(changed_departments) > max_to_show:
                message += f'  ... и еще {len(changed_departments) - max_to_show} отделов\n\n'
            
            message += f'\nВы уверены, что хотите создать {report_type} с измененными данными?'
            
            reply = QMessageBox.question(
                self, 
                f'Предупреждение: измененные данные',
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes
        else:
            # Рапорты есть, но без изменений данных
            reply = QMessageBox.question(
                self, 
                f'Внимание: имеются рапорты',
                f'За выбранный месяц имеются рапорты.\n\n'
                f'{report_type.capitalize()} будет создан с данными, измененными рапортами.\n\n'
                f'Продолжить создание {report_type}?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply == QMessageBox.Yes


    def recalculate_pending_rows(self):
        """Пересчитывает все строки, ожидающие обновления"""
        for row in self.pending_recalculations:
            self.recalculate_decades_and_total(row)
        self.pending_recalculations.clear()
        
        if self.department_num is None:
            QTimer.singleShot(50, self.update_totals_row)

    def create_old_report(self):
        """Создает отчет в старом формате (как в govno.py) с проверкой рапортов"""
        try:
            if not self._check_reports_warning("отчет"):
                return
                
            progress = QProgressDialog("Создание отчета в старом формате...", 
                                      "Отмена", 0, 100, self)
            progress.setWindowTitle("Генерация отчета")
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.show()
            
            self.worker_thread = WorkerThread('generate_report')
            self.worker_thread.progress.connect(progress.setValue)
            self.worker_thread.finished.connect(
                lambda: self.on_create_old_report_finished(progress)
            )
            self.worker_thread.error.connect(
                lambda e: self._on_report_error(e, progress, "отчета")
            )
            self.worker_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании отчета:\n{str(e)}')

    def on_create_old_report_finished(self, progress):
        """Вызывается после завершения потока генерации отчета"""
        progress.close()
        
        # Запускаем фактическую генерацию отчета
        try:
            generator = OldReportGenerator(self.db, self.date)
            success, message = generator.create_report()
            
            if success:
                QMessageBox.information(self, 'Успех', message)
            else:
                QMessageBox.warning(self, 'Ошибка', message)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании отчета:\n{str(e)}')

    def on_create_old_report_error(self, error_msg, progress):
        """Вызывается при ошибке генерации отчета"""
        progress.close()
        QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании отчета:\n{error_msg}')

    def generate_svodka(self):
        """Создание сводки Excel из текущих данных"""
        try:
            if not self._check_reports_warning("сводку"):
                return
                
            progress = QProgressDialog("Создание сводки...", "Отмена", 0, 100, self)
            progress.setWindowTitle("Генерация отчета")
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.show()
            
            self.worker_thread = WorkerThread('generate_report')
            self.worker_thread.progress.connect(progress.setValue)
            self.worker_thread.finished.connect(
                lambda: self._on_generate_report_finished(progress)
            )
            self.worker_thread.error.connect(
                lambda e: self._on_report_error(e, progress, "сводки")
            )
            self.worker_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании сводки:\n{str(e)}')

    def _on_generate_report_finished(self, progress):
        """Вызывается после завершения генерации сводки"""
        progress.close()
        try:
            from report_generator import create_svodka_from_database
            from config import DB_PATH
            
            result = create_svodka_from_database(DB_PATH, self.date)
            
            if result:
                QMessageBox.information(self, 'Успех', f'Сводка создана:\n{result}')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось создать сводку')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании сводки:\n{str(e)}')
                                 
    def _on_report_error(self, error_msg, progress, report_type):
        """Обработчик ошибок генерации отчетов"""
        progress.close()
        QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании {report_type}:\n{error_msg}')

    def recalculate_decades_and_total(self, row):
        """Оптимизированный пересчет значений декад и итогов"""
        try:
            self.table.blockSignals(True)
            
            # Предварительная проверка наличия строки
            if row >= self.table.rowCount():
                return
            
            # Используем локальные переменные для скорости
            table = self.table
            decade_sums = [0.0, 0.0, 0.0]
            day_ranges = [(0, 10), (10, 20), (20, 31)]
            
            for decade_idx, (start, end) in enumerate(day_ranges):
                for col in range(start, end):
                    item = table.item(row, col)
                    if item and item.text():
                        try:
                            decade_sums[decade_idx] += float(item.text())
                        except ValueError:
                            pass
            
            total_sum = sum(decade_sums)
            
            # Обновляем ячейки декад и итога
            decade_cols = [31, 32, 33, 34]
            values = decade_sums + [total_sum]
            
            for col, value in zip(decade_cols, values):
                item = table.item(row, col)
                if not item:
                    item = QTableWidgetItem()
                    table.setItem(row, col, item)
                item.setText(f"{value:.2f}".rstrip('0').rstrip('.') if value != 0 else "")
                
        except Exception as e:
            print(f"Ошибка при пересчете декад: {e}")
        finally:
            self.table.blockSignals(False)

    def load_data(self):
        """Оптимизированная загрузка данных"""
        self.is_loading_data = True
        self.table.blockSignals(True)
    
        try:
            cursor = self.db.conn.cursor()
            month_year = self.date.replace('.', '/')
        
        # Кэшируем запросы
            if self.department_num:
                departments = [(self.department_num,)]
                dept_where = "WHERE number = ?"
                dept_params = (self.department_num,)
            else:
                departments = cursor.execute(
                    'SELECT number FROM departments ORDER BY number'
                ).fetchall()
                dept_where = ""
                dept_params = ()
        
            row_count = len(departments)
            if self.department_num is None:
                row_count += 1
        
            self.table.setRowCount(row_count)
            self.table.setColumnCount(35)
        
        # Устанавливаем заголовки
            headers = [str(day) for day in range(1, 32)]
            headers.extend(['Декада 1', 'Декада 2', 'Декада 3', 'Итог'])
            self.table.setHorizontalHeaderLabels(headers)
        
        # Подготавливаем вертикальные заголовки
            vertical_headers = []
            for dept in departments:
                dept_num = dept[0]
                comment = cursor.execute(
                    f'SELECT comment FROM departments {dept_where}',
                    dept_params if dept_where else ()
                ).fetchone()[0]
                vertical_headers.append(f"{dept_num} - {comment}")
        
            if self.department_num is None:
                vertical_headers.append("ИТОГ")
        
            self.table.setVerticalHeaderLabels(vertical_headers)
        
            self.dept_id_to_row = {}
        
        # Заполняем таблицу данными
            for row_idx, dept in enumerate(departments):
                dept_num = dept[0]
                cursor.execute('SELECT id FROM departments WHERE number = ?', (dept_num,))
                result = cursor.fetchone()
                if not result:
                    continue
                
                dept_id = result[0]
                self.dept_id_to_row[dept_id] = row_idx
            
            # Используем метод для получения данных с рапортами
                daily_data = self.db.get_daily_data_with_reports(dept_id, month_year)
            
                total_month = 0
                for day in range(1, 32):
                    value = daily_data.get(day, 0)
                    total_month += value
                
                    item = QTableWidgetItem(str(value) if value != 0 else "")
                    self.table.setItem(row_idx, day-1, item)
            
            # Вычисляем декады
                decade1 = sum(daily_data.get(day, 0) for day in range(1, 11))
                decade2 = sum(daily_data.get(day, 0) for day in range(11, 21))
                decade3 = sum(daily_data.get(day, 0) for day in range(21, 32))
            
            # Получаем цвета для декад
                monthly_data = cursor.execute('''
                    SELECT decade1_color, decade2_color, decade3_color, total_color 
                    FROM monthly_data WHERE department_id = ? AND month_year = ?
                ''', (dept_id, month_year)).fetchone()
            
                colors = monthly_data if monthly_data else (None, None, None, None)
            
            # Заполняем декады и итог
                for i, (value, color) in enumerate(
                    [(decade1, colors[0]), (decade2, colors[1]), 
                     (decade3, colors[2]), (total_month, colors[3])], 
                    start=31
                ):
                    item = QTableWidgetItem(str(value) if value != 0 else "")
                    if color and color != "#000000":
                        item.setBackground(QColor(color))
                    self.table.setItem(row_idx, i, item)
        
        # Добавляем строку итогов, если показываем все отделы
            if self.department_num is None:
                self.update_totals_row()
        
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.table.cellDoubleClicked.connect(self.cell_double_clicked)
        
            self.table.setToolTip("Двойной щелчок по ячейке для изменения цвета\nF1 - сохранить изменения, F2 - обновить данные")
        
            self.update_save_button_visibility()
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {str(e)}')
        finally:
            self.table.blockSignals(False)
            self.is_loading_data = False

    def initUI(self):
        self.setWindowTitle('Результаты поиска')
        self.showMaximized()
        self.setStyleSheet(APP_STYLE)
        
        self.settings = QSettings('Milkman', 'SearchResultWindow')
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Заголовок
        if self.department_num:
            title_text = f'Данные за {get_month_name(self.date)} {self.date} - Подразделение {self.department_num}'
        else:
            title_text = f'Данные за {get_month_name(self.date)} {self.date} - Все подразделения'
        
        title_label = QLabel(title_text)
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; padding: 5px;")
        title_label.setMaximumHeight(40)
        main_layout.addWidget(title_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Сплиттер
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть
        self.left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_widget.setLayout(left_layout)
        
        # Правая часть
        self.right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_widget.setLayout(right_layout)
        
        # Таблица результатов
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellChanged.connect(self.on_cell_changed)
        right_layout.addWidget(self.table)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.reload_btn = QPushButton('Обновить данные')
        self.reload_btn.clicked.connect(self.reload_data)
        self.reload_btn.setStyleSheet("background-color: #3498db;")
        button_layout.addWidget(self.reload_btn)
        
        self.reports_mode_btn = QPushButton('Показать рапорты')
        self.reports_mode_btn.clicked.connect(self.toggle_reports_mode)
        self.reports_mode_btn.setStyleSheet("background-color: #9b59b6;")
        button_layout.addWidget(self.reports_mode_btn)
        
        self.save_btn = QPushButton('Сохранить изменения')
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setStyleSheet("background-color: #27ae60;")
        button_layout.addWidget(self.save_btn)
        
        self.save_warning_label = QLabel('Невозможно сохранить изменения: существуют рапорты')
        self.save_warning_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 8px; background-color: #ffe6e6; border-radius: 4px;")
        self.save_warning_label.setVisible(False)
        button_layout.addWidget(self.save_warning_label)
        
        button_layout.addStretch()
        
        self.generate_report_btn = QPushButton('Создать сводку Excel')
        self.generate_report_btn.clicked.connect(self.generate_svodka)
        self.generate_report_btn.setStyleSheet("background-color: #27ae60;")
        button_layout.addWidget(self.generate_report_btn)
        
        self.create_report_btn = QPushButton('Создать отчет (старый формат)')
        self.create_report_btn.clicked.connect(self.create_old_report)
        self.create_report_btn.setStyleSheet("background-color: #16a085;")
        button_layout.addWidget(self.create_report_btn)
        
        self.close_btn = QPushButton('Закрыть')
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("background-color: #e74c3c;")
        button_layout.addWidget(self.close_btn)

        right_layout.addLayout(button_layout)
        
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        
        splitter_sizes = self.settings.value('splitter_sizes')
        if splitter_sizes:
            self.splitter.setSizes([int(size) for size in splitter_sizes])
        else:
            self.splitter.setSizes([0, 1])
        
        self.left_widget.setMinimumWidth(200)
        self.right_widget.setMinimumWidth(400)
        
        main_layout.addWidget(self.splitter, 1)
        self.setLayout(main_layout)
        
        window_size = self.settings.value('window_size')
        if window_size:
            self.resize(window_size)
    
    def update_save_button_visibility(self):
        """Обновляет видимость кнопки сохранения в зависимости от наличия рапортов"""
        month_year = self.date.replace('.', '/')
        reports_exist = self.db.check_reports_exist(month_year)
        
        if reports_exist:
            # Если есть рапорты - скрываем кнопку и показываем предупреждение
            self.save_btn.setVisible(False)
            self.save_warning_label.setVisible(True)
        else:
            # Если нет рапортов - показываем кнопку и скрываем предупреждение
            self.save_btn.setVisible(True)
            self.save_warning_label.setVisible(False)
    
    def closeEvent(self, event):
        # Сохраняем размер окна и сплиттера
        self.settings.setValue('window_size', self.size())
        self.settings.setValue('splitter_sizes', self.splitter.sizes())
        super().closeEvent(event)
    
    def on_cell_changed(self, row, col):
        """Обработчик изменения ячейки таблицы"""
        if self.is_loading_data:
            return
            
        if self.department_num is None and row == self.table.rowCount() - 1:
            return
        
        if col < 31:
            # Проверяем введенное значение
            item = self.table.item(row, col)
            if item and item.text():
                try:
                    float(item.text())
                except ValueError:
                    QMessageBox.warning(self, 'Ошибка ввода', 
                                      f'В ячейке [Строка {row+1}, День {col+1}] введено нечисловое значение: "{item.text()}"\nПожалуйста, введите число.')
                    # Сбрасываем значение
                    self.table.blockSignals(True)
                    item.setText("")
                    self.table.blockSignals(False)
                    return
            
            # Добавляем строку в список для отложенного пересчета
            self.pending_recalculations.add(row)
            # Запускаем таймер (300 мс) для отложенного пересчета
            self.recalculate_timer.start(300)
    
    def recalculate_decades_and_total(self, row):
        """Пересчитывает значения декад и итогов для указанной строки"""
        try:
            # Отключаем сигналы для предотвращения рекурсии
            self.table.blockSignals(True)
            
            # Сумма за декаду 1 (дни 1-10, индексы 0-9)
            decade1_sum = 0
            for col in range(0, 10):
                item = self.table.item(row, col)
                if item and item.text():
                    try:
                        decade1_sum += float(item.text())
                    except ValueError:
                        # Если не число, игнорируем
                        pass
            
            # Сумма за декаду 2 (дни 11-20, индексы 10-19)
            decade2_sum = 0
            for col in range(10, 20):
                item = self.table.item(row, col)
                if item and item.text():
                    try:
                        decade2_sum += float(item.text())
                    except ValueError:
                        # Если не число, игнорируем
                        pass
            
            # Сумма за декаду 3 (дни 21-31, индексы 20-30)
            decade3_sum = 0
            for col in range(20, 31):
                item = self.table.item(row, col)
                if item and item.text():
                    try:
                        decade3_sum += float(item.text())
                    except ValueError:
                        # Если не число, игнорируем
                        pass
            
            # Общая сумма за месяц
            total_sum = decade1_sum + decade2_sum + decade3_sum
            
            # Обновляем ячейки декад и итога без генерации событий
            self.table.blockSignals(True)
            try:
                for i, value in [(31, decade1_sum), (32, decade2_sum), (33, decade3_sum), (34, total_sum)]:
                    item = self.table.item(row, i)
                    if not item:
                        item = QTableWidgetItem()
                        self.table.setItem(row, i, item)
                    item.setText(str(value) if value != 0 else "")
            finally:
                self.table.blockSignals(False)
                
        except Exception as e:
            print(f"Ошибка при пересчете декад: {e}")
        finally:
            self.table.blockSignals(False)
    
    def update_totals_row(self):
        """Обновляет строку итогов для всех подразделений"""
        if self.department_num is not None:
            return
        
        total_row = self.table.rowCount() - 1
        self.table.blockSignals(True)
        
        try:
            # Сбрасываем все суммы
            for col in range(self.table.columnCount()):
                item = self.table.item(total_row, col)
                if not item:
                    item = QTableWidgetItem("0")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QColor(230, 240, 255))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                    self.table.setItem(total_row, col, item)
                else:
                    item.setText("0")
            
            # Суммируем по всем строкам (кроме строки итогов)
            for row in range(total_row):
                for col in range(self.table.columnCount()):
                    source_item = self.table.item(row, col)
                    if source_item and source_item.text():
                        try:
                            value = float(source_item.text())
                            total_item = self.table.item(total_row, col)
                            current_total = float(total_item.text()) if total_item.text() else 0
                            total_item.setText(str(current_total + value))
                        except ValueError:
                            # Если не число, игнорируем
                            pass
        finally:
            self.table.blockSignals(False)
    
    def toggle_reports_mode(self):
        if self.reports_window is None:
            self.show_reports_window()
        else:
            self.hide_reports_window()
    
    def show_reports_window(self):
        self.reports_window = ReportsWindow(self.db, self.date, self)
        self.left_widget.layout().addWidget(self.reports_window)
        self.left_widget.setVisible(True)
        self.reports_mode_btn.setText('Скрыть рапорты')
        
        reports_width = self.settings.value('reports_width')
        if reports_width:
            total_width = self.splitter.width()
            self.splitter.setSizes([int(reports_width), total_width - int(reports_width)])
        else:
            total_width = self.splitter.width()
            self.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])
    
    def hide_reports_window(self):
        if self.reports_window:
            self.settings.setValue('reports_width', self.splitter.sizes()[0])
            
            self.left_widget.layout().removeWidget(self.reports_window)
            self.reports_window.deleteLater()
            self.reports_window = None
        
        self.splitter.setSizes([0, 1])
        self.reports_mode_btn.setText('Показать рапорты')
    
    def update_data_from_report(self, department_id, day, delta):
        """Обновляет данные в таблице на основе изменений из рапорта"""
        row = self.dept_id_to_row.get(department_id)
        if row is not None:
            item = self.table.item(row, day-1)
            if item:
                try:
                    current_value = float(item.text()) if item.text() else 0
                    new_value = current_value + delta
                    new_value = max(0, new_value)
                    
                    self.table.blockSignals(True)
                    item.setText(str(new_value) if new_value != 0 else "")
                    self.table.blockSignals(False)
                    
                    self.pending_recalculations.add(row)
                    self.recalculate_timer.start(300)
                    
                except Exception as e:
                    print(f"Ошибка при обновлении данных из рапорта: {e}")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            # Проверяем наличие рапортов перед сохранением
            month_year = self.date.replace('.', '/')
            if self.db.check_reports_exist(month_year):
                QMessageBox.warning(self, 'Предупреждение', 
                                  'Невозможно сохранить изменения: существуют рапорты.\nУдалите все рапорты перед сохранением.')
            else:
                self.save_data()
        elif event.key() == Qt.Key_F2:
            self.reload_data()
        else:
            super().keyPressEvent(event)
    
    def show_context_menu(self, position):
        selected_items = self.table.selectedItems()
        context_menu = QMenu(self)
        
        if selected_items:
            change_color_action = QAction("Изменить цвет выделенных ячеек", self)
            change_color_action.triggered.connect(lambda: self.change_selected_cells_color(selected_items))
            context_menu.addAction(change_color_action)
            
            reset_color_action = QAction("Сбросить цвет выделенных ячеек", self)
            reset_color_action.triggered.connect(lambda: self.reset_selected_cells_color(selected_items))
            context_menu.addAction(reset_color_action)
            
            context_menu.addSeparator()
        
        # Проверяем наличие рапортов для пункта меню "Сохранить"
        month_year = self.date.replace('.', '/')
        reports_exist = self.db.check_reports_exist(month_year)
        
        save_action = QAction("Сохранить изменения (F1)", self)
        save_action.triggered.connect(self.save_data)
        save_action.setEnabled(not reports_exist)  # Отключаем если есть рапорты
        context_menu.addAction(save_action)
        
        reload_action = QAction("Обновить данные (F2)", self)
        reload_action.triggered.connect(self.reload_data)
        context_menu.addAction(reload_action)
        
        if context_menu.actions():
            context_menu.exec_(self.table.viewport().mapToGlobal(position))
    
    def change_selected_cells_color(self, selected_items):
        color = QColorDialog.getColor()
        if color.isValid():
            if color == QColor(0, 0, 0) or color == QColor(255, 255, 255):
                for item in selected_items:
                    item.setBackground(QColor(255, 255, 255))
            else:
                for item in selected_items:
                    item.setBackground(color)
    
    def reset_selected_cells_color(self, selected_items):
        for item in selected_items:
            item.setBackground(QColor(255, 255, 255))
    
    def on_generate_report_finished(self, progress):
        progress.close()
        
        # Запускаем фактическую генерацию отчета
        try:
            from report_generator import create_svodka_from_database
            from config import DB_PATH
            
            result = create_svodka_from_database(DB_PATH, self.date)
            
            if result:
                QMessageBox.information(self, 'Успех', f'Сводка создана:\n{result}')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось создать сводку')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании сводки:\n{str(e)}')
    
    def on_generate_report_error(self, error_msg, progress):
        progress.close()
        QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании сводки:\n{error_msg}')
    
    def reload_data(self):
        """Обновление данных с прогресс-баром"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker_thread = WorkerThread('load_data')
        self.worker_thread.progress.connect(self.progress_bar.setValue)
        self.worker_thread.finished.connect(self.on_reload_finished)
        self.worker_thread.error.connect(self.on_reload_error)
        self.worker_thread.start()
    
    def on_reload_finished(self):
        # Загружаем данные после завершения потока
        self.load_data()
        self.progress_bar.setValue(100)
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        QMessageBox.information(self, 'Обновление', 'Данные успешно обновлены из базы данных!')
    
    def on_reload_error(self, error_msg):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Ошибка', f'Ошибка при обновлении данных:\n{error_msg}')
    
    def save_data(self):
        """Сохранение данных с прогресс-баром"""
        # Проверяем наличие рапортов перед сохранением
        month_year = self.date.replace('.', '/')
        if self.db.check_reports_exist(month_year):
            QMessageBox.warning(self, 'Предупреждение', 
                              'Невозможно сохранить изменения: существуют рапорты.\nУдалите все рапорты перед сохранением.')
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker_thread = WorkerThread('save_data')
        self.worker_thread.progress.connect(self.progress_bar.setValue)
        self.worker_thread.finished.connect(self.on_save_finished)
        self.worker_thread.error.connect(self.on_save_error)
        self.worker_thread.start()
    
    def on_save_finished(self):
        # Выполняем фактическое сохранение после завершения потока
        self.actual_save_data()
        self.progress_bar.setValue(100)
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        QMessageBox.information(self, 'Успех', 'Данные сохранены!')
    
    def on_save_error(self, error_msg):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Ошибка', f'Ошибка при сохранении:\n{error_msg}')
    
    def actual_save_data(self):
        """Фактическая логика сохранения данных"""
        cursor = self.db.conn.cursor()
        
        try:
            month_year = self.date.replace('.', '/')  # Добавляем определение month_year
            
            save_rows = self.table.rowCount()
            if self.department_num is None:
                save_rows -= 1
            
            for row in range(save_rows):
                header = self.table.verticalHeaderItem(row).text()
                # Проверяем, что заголовок содержит номер отдела
                if ' - ' in header:
                    dept_num_str = header.split(' - ')[0]
                    try:
                        dept_num = int(dept_num_str)
                    except ValueError:
                        QMessageBox.warning(self, 'Ошибка', f'Неверный номер отдела в строке {row+1}: "{dept_num_str}"')
                        continue
                else:
                    QMessageBox.warning(self, 'Ошибка', f'Неверный формат заголовка в строке {row+1}')
                    continue
                
                dept_id = cursor.execute('SELECT id FROM departments WHERE number = ?', (dept_num,)).fetchone()[0]
                
                for day in range(1, 32):
                    item = self.table.item(row, day-1)
                    if item:
                        # Проверяем значение перед сохранением
                        if item.text():
                            try:
                                value = float(item.text())
                            except ValueError:
                                QMessageBox.warning(self, 'Ошибка', f'Нечисловое значение в строке {row+1}, день {day}: "{item.text()}"')
                                continue
                        else:
                            value = 0
                        
                        bg_color = item.background()
                        color = None
                        if bg_color != Qt.NoBrush and bg_color.color() != QColor(255, 255, 255):
                            color = bg_color.color().name()
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO daily_data 
                            (department_id, date, day, value, color)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (dept_id, f"01/{month_year}", day, value, color))
                
                # Сохраняем данные по декадам
                decade1_item = self.table.item(row, 31)
                decade2_item = self.table.item(row, 32)
                decade3_item = self.table.item(row, 33)
                total_item = self.table.item(row, 34)
                
                # Проверяем значения декад
                try:
                    decade1 = float(decade1_item.text()) if decade1_item and decade1_item.text() else 0
                    decade2 = float(decade2_item.text()) if decade2_item and decade2_item.text() else 0
                    decade3 = float(decade3_item.text()) if decade3_item and decade3_item.text() else 0
                    total = float(total_item.text()) if total_item and total_item.text() else 0
                except ValueError:
                    QMessageBox.warning(self, 'Ошибка', f'Нечисловое значение в строке {row+1} в столбцах декад')
                    continue
                
                decade1_color = None
                decade2_color = None
                decade3_color = None
                total_color = None
                
                if decade1_item:
                    bg_color = decade1_item.background()
                    if bg_color != Qt.NoBrush and bg_color.color() != QColor(255, 255, 255):
                        decade1_color = bg_color.color().name()
                
                if decade2_item:
                    bg_color = decade2_item.background()
                    if bg_color != Qt.NoBrush and bg_color.color() != QColor(255, 255, 255):
                        decade2_color = bg_color.color().name()
                
                if decade3_item:
                    bg_color = decade3_item.background()
                    if bg_color != Qt.NoBrush and bg_color.color() != QColor(255, 255, 255):
                        decade3_color = bg_color.color().name()
                
                if total_item:
                    bg_color = total_item.background()
                    if bg_color != Qt.NoBrush and bg_color.color() != QColor(255, 255, 255):
                        total_color = bg_color.color().name()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO monthly_data 
                    (department_id, month_year, decade1, decade2, decade3, total,
                     decade1_color, decade2_color, decade3_color, total_color)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (dept_id, month_year, decade1, decade2, decade3, total,
                      decade1_color, decade2_color, decade3_color, total_color))
            
            self.db.conn.commit()
            
        except Exception as e:
            self.db.conn.rollback()
            raise e
    
    def load_data(self):
        """Загрузка данных с защитой от зависания"""
        self.is_loading_data = True
        self.table.blockSignals(True)
        
        try:
            cursor = self.db.conn.cursor()
            month_year = self.date.replace('.', '/')
            
            if self.department_num:
                departments = [(self.department_num,)]
            else:
                departments = cursor.execute('SELECT number FROM departments ORDER BY number').fetchall()
            
            row_count = len(departments)
            if self.department_num is None:
                row_count += 1
            
            self.table.setRowCount(row_count)
            self.table.setColumnCount(35)
            
            headers = [str(day) for day in range(1, 32)]
            headers.extend(['Декада 1', 'Декада 2', 'Декада 3', 'Итог'])
            
            self.table.setHorizontalHeaderLabels(headers)
            
            # Создаем заголовки строк
            vertical_headers = []
            for dept in departments:
                dept_num = dept[0]
                comment = cursor.execute('SELECT comment FROM departments WHERE number = ?', (dept_num,)).fetchone()[0]
                vertical_headers.append(f"{dept_num} - {comment}")
            
            if self.department_num is None:
                vertical_headers.append("ИТОГ")
            
            self.table.setVerticalHeaderLabels(vertical_headers)
            
            self.dept_id_to_row = {}
            
            # Заполняем таблицу данными
            for row_idx, dept in enumerate(departments):
                dept_num = dept[0]
                dept_id = cursor.execute('SELECT id FROM departments WHERE number = ?', (dept_num,)).fetchone()[0]
                
                self.dept_id_to_row[dept_id] = row_idx
                
                # Загружаем ежедневные данные
                daily_data = cursor.execute('''
                    SELECT day, value, color FROM daily_data 
                    WHERE department_id = ? AND date LIKE ?
                ''', (dept_id, f'%/{month_year}')).fetchall()
                
                day_data_dict = {day: (value, color) for day, value, color in daily_data}
                
                # Загружаем данные из рапортов
                reports_data = cursor.execute('''
                    SELECT day1, day2, day3, day4, day5, day6, day7, day8, day9, day10,
                           day11, day12, day13, day14, day15, day16, day17, day18, day19, day20,
                           day21, day22, day23, day24, day25, day26, day27, day28, day29, day30, day31
                    FROM reports 
                    WHERE department_id = ? AND date LIKE ?
                ''', (dept_id, f'%/{month_year}')).fetchall()
                
                # Применяем изменения из рапортов
                for report in reports_data:
                    for day in range(1, 32):
                        delta_str = report[day-1]
                        if delta_str:
                            try:
                                delta = float(delta_str)
                                current_value, color = day_data_dict.get(day, (0, None))
                                new_value = current_value + delta
                                new_value = max(0, new_value)
                                day_data_dict[day] = (new_value, color)
                            except ValueError:
                                # Если в рапорте не число, игнорируем
                                pass
                
                total_month = 0
                for day in range(1, 32):
                    value, color = day_data_dict.get(day, (0, None))
                    total_month += value
                    
                    item = QTableWidgetItem(str(value) if value != 0 else "")
                    if color and color != "#000000":
                        item.setBackground(QColor(color))
                    self.table.setItem(row_idx, day-1, item)
                
                # Вычисляем декады
                decade1 = sum(day_data_dict.get(day, (0, None))[0] for day in range(1, 11))
                decade2 = sum(day_data_dict.get(day, (0, None))[0] for day in range(11, 21))
                decade3 = sum(day_data_dict.get(day, (0, None))[0] for day in range(21, 32))
                
                monthly_data = cursor.execute('''
                    SELECT decade1_color, decade2_color, decade3_color, total_color 
                    FROM monthly_data WHERE department_id = ? AND month_year = ?
                ''', (dept_id, month_year)).fetchone()
                
                colors = monthly_data if monthly_data else (None, None, None, None)
                
                # Заполняем декады и итог
                item = QTableWidgetItem(str(decade1) if decade1 != 0 else "")
                if colors[0] and colors[0] != "#000000":
                    item.setBackground(QColor(colors[0]))
                self.table.setItem(row_idx, 31, item)
                
                item = QTableWidgetItem(str(decade2) if decade2 != 0 else "")
                if colors[1] and colors[1] != "#000000":
                    item.setBackground(QColor(colors[1]))
                self.table.setItem(row_idx, 32, item)
                
                item = QTableWidgetItem(str(decade3) if decade3 != 0 else "")
                if colors[2] and colors[2] != "#000000":
                    item.setBackground(QColor(colors[2]))
                self.table.setItem(row_idx, 33, item)
                
                item = QTableWidgetItem(str(total_month) if total_month != 0 else "")
                if colors[3] and colors[3] != "#000000":
                    item.setBackground(QColor(colors[3]))
                self.table.setItem(row_idx, 34, item)
            
            # Добавляем строку итогов, если показываем все отделы
            if self.department_num is None:
                self.update_totals_row()
            
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.table.cellDoubleClicked.connect(self.cell_double_clicked)
            
            self.table.setToolTip("Двойной щелчок по ячейке для изменения цвета\nF1 - сохранить изменения, F2 - обновить данные")
            
            # Обновляем видимость кнопки сохранения
            self.update_save_button_visibility()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {str(e)}')
        finally:
            self.table.blockSignals(False)
            self.is_loading_data = False
    
    def cell_double_clicked(self, row, col):
        if self.department_num is None and row == self.table.rowCount() - 1:
            return
            
        item = self.table.item(row, col)
        if item is None:
            return
            
        color = QColorDialog.getColor()
        if color.isValid():
            if color == QColor(0, 0, 0) or color == QColor(255, 255, 255):
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(color)