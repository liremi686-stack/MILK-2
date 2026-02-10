import sqlite3
from config import DB_PATH, DEFAULT_DEPARTMENTS
import logging
from logging_config import log_database_error

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.create_tables()
            self.create_departments()  # Теперь этот метод существует
            logger.info(f"Подключение к базе данных успешно: {DB_PATH}")
        except sqlite3.Error as e:
            log_database_error(logger, e, "Подключение к базе данных")
            raise
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY,
                    number INTEGER UNIQUE,
                    comment TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_id INTEGER,
                    date TEXT,
                    day INTEGER,
                    value REAL,
                    color TEXT,
                    FOREIGN KEY (department_id) REFERENCES departments (id),
                    UNIQUE(department_id, date, day)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monthly_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_id INTEGER,
                    month_year TEXT,
                    decade1 REAL,
                    decade2 REAL,
                    decade3 REAL,
                    total REAL,
                    decade1_color TEXT,
                    decade2_color TEXT,
                    decade3_color TEXT,
                    total_color TEXT,
                    FOREIGN KEY (department_id) REFERENCES departments (id),
                    UNIQUE(department_id, month_year)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_number INTEGER,
                    department_id INTEGER,
                    date TEXT,
                    day1 TEXT, day2 TEXT, day3 TEXT, day4 TEXT, day5 TEXT,
                    day6 TEXT, day7 TEXT, day8 TEXT, day9 TEXT, day10 TEXT,
                    day11 TEXT, day12 TEXT, day13 TEXT, day14 TEXT, day15 TEXT,
                    day16 TEXT, day17 TEXT, day18 TEXT, day19 TEXT, day20 TEXT,
                    day21 TEXT, day22 TEXT, day23 TEXT, day24 TEXT, day25 TEXT,
                    day26 TEXT, day27 TEXT, day28 TEXT, day29 TEXT, day30 TEXT,
                    day31 TEXT,
                    FOREIGN KEY (department_id) REFERENCES departments (id)
                )
            ''')
            
            self.conn.commit()
            logger.debug("Таблицы базы данных созданы/проверены")
            
        except sqlite3.Error as e:
            log_database_error(logger, e, "Создание таблиц")
            self.conn.rollback()
            raise
    
    def create_departments(self):
        """Заполняет таблицу departments данными по умолчанию"""
        cursor = self.conn.cursor()
        try:
            # Проверяем, есть ли уже данные в таблице
            cursor.execute('SELECT COUNT(*) FROM departments')
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Вставляем данные по умолчанию
                for number, comment in DEFAULT_DEPARTMENTS:
                    cursor.execute('INSERT INTO departments (number, comment) VALUES (?, ?)', 
                                  (number, comment))
                self.conn.commit()
                logger.info("Таблица departments заполнена данными по умолчанию")
            else:
                logger.debug(f"Таблица departments уже содержит {count} записей")
                
        except sqlite3.Error as e:
            log_database_error(logger, e, "Заполнение таблицы departments")
            self.conn.rollback()
            raise

    def create_report(self, department_id, date):
        """Создает новый рапорт и возвращает его номер"""
        cursor = self.conn.cursor()
        
        # Получаем максимальный номер рапорта для указанного месяца
        cursor.execute('''
            SELECT MAX(report_number) FROM reports 
            WHERE date LIKE ?
        ''', (f'%/{date.split("/")[1]}',))
        
        result = cursor.fetchone()
        max_report_number = result[0] if result[0] else 0
        new_report_number = max_report_number + 1
        
        # Создаем рапорт
        cursor.execute('''
            INSERT INTO reports (report_number, department_id, date)
            VALUES (?, ?, ?)
        ''', (new_report_number, department_id, date))
        
        self.conn.commit()
        logger.info(f"Создан рапорт №{new_report_number} для отдела {department_id}, дата {date}")
        
        return new_report_number

    def update_report_day(self, report_id, day, value):
        cursor = self.conn.cursor()
        if 1 <= day <= 31:  # Проверка диапазона
            try:
                column_name = f"day{day}"
                cursor.execute(f'UPDATE reports SET {column_name} = ? WHERE id = ?', (value, report_id))
                self.conn.commit()
                logger.debug(f"Обновлен рапорт {report_id}, день {day}: {value}")
            except sqlite3.Error as e:
                log_database_error(logger, e, f"UPDATE reports SET {column_name}", (value, report_id))
                raise
        else:
            error_msg = f"Недопустимый день: {day}. Должен быть от 1 до 31"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_all_reports(self, month_year):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.id, r.report_number, d.comment, 
                   r.day1, r.day2, r.day3, r.day4, r.day5, r.day6, r.day7, r.day8, r.day9, r.day10,
                   r.day11, r.day12, r.day13, r.day14, r.day15, r.day16, r.day17, r.day18, r.day19, r.day20,
                   r.day21, r.day22, r.day23, r.day24, r.day25, r.day26, r.day27, r.day28, r.day29, r.day30, r.day31
            FROM reports r
            JOIN departments d ON r.department_id = d.id
            WHERE r.date LIKE ?
            ORDER BY r.report_number
        ''', (f'%/{month_year}',))
        return cursor.fetchall()
    
    def get_report_by_id(self, report_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.id, r.report_number, r.department_id, d.comment, 
                   r.day1, r.day2, r.day3, r.day4, r.day5, r.day6, r.day7, r.day8, r.day9, r.day10,
                   r.day11, r.day12, r.day13, r.day14, r.day15, r.day16, r.day17, r.day18, r.day19, r.day20,
                   r.day21, r.day22, r.day23, r.day24, r.day25, r.day26, r.day27, r.day28, r.day29, r.day30, r.day31
            FROM reports r
            JOIN departments d ON r.department_id = d.id
            WHERE r.id = ?
        ''', (report_id,))
        return cursor.fetchone()
    
    def delete_report(self, report_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM reports WHERE id = ?', (report_id,))
        self.conn.commit()
    
    def get_departments_list(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT number, comment FROM departments ORDER BY number')
        return cursor.fetchall()
    
    def check_reports_exist(self, month_year):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM reports WHERE date LIKE ?', (f'%/{month_year}',))
        count = cursor.fetchone()[0]
        return count > 0
    
    def get_daily_data_with_reports(self, department_id, month_year):
        """Получает ежедневные данные с учетом изменений из рапортов"""
        cursor = self.conn.cursor()
    
        # Получаем базовые данные
        cursor.execute('''
            SELECT day, value FROM daily_data 
            WHERE department_id = ? AND date LIKE ?
            ORDER BY day
        ''', (department_id, f'%/{month_year}'))
    
        daily_data = {day: value for day, value in cursor.fetchall()}
    
        # Получаем изменения из рапортов
        cursor.execute('''
            SELECT day1, day2, day3, day4, day5,
                   day6, day7, day8, day9, day10,
                   day11, day12, day13, day14, day15,
                   day16, day17, day18, day19, day20,
                   day21, day22, day23, day24, day25,
                   day26, day27, day28, day29, day30, day31
            FROM reports 
            WHERE department_id = ? AND date LIKE ?
        ''', (department_id, f'%/{month_year}'))
    
        reports_data = cursor.fetchall()
    
        # Применяем изменения из рапортов
        for report in reports_data:
            for day_idx, delta_str in enumerate(report, 1):
                if delta_str and delta_str.strip():
                    try:
                        delta = float(delta_str)
                        current = daily_data.get(day_idx, 0)
                        daily_data[day_idx] = current + delta
                    except ValueError:
                        continue
    
        return daily_data