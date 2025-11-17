import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_file: str = r'Telegram_bots\tango_bot\tango_database.db'):
        self.db_file = db_file
        self.init_database()
        
    @contextmanager
    def get_connection(self):
        """Context manager для безпечної роботи з БД"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Для доступу по імені колонки
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Ініціалізація таблиць бази даних"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблиця менторів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mentors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mentor_name TEXT NOT NULL,
                    user_id TEXT UNIQUE NOT NULL,
                    profile_url TEXT NOT NULL,
                    telegram_username TEXT,
                    telegram_chat_id INTEGER,
                    instagram_url TEXT,
                    activation_code TEXT UNIQUE,
                    last_assigned_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця видалених менторів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deleted_mentors (
                    id INTEGER PRIMARY KEY,
                    mentor_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    profile_url TEXT NOT NULL,
                    telegram_username TEXT,
                    telegram_chat_id INTEGER,
                    instagram_url TEXT,
                    last_assigned_at TIMESTAMP,
                    created_at TIMESTAMP,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця стрімерів
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS streamers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user_id TEXT UNIQUE NOT NULL,
                    profile_url TEXT NOT NULL,
                    tg_name TEXT,
                    tg_url TEXT,
                    instagram_url TEXT,
                    platform TEXT,
                    mentor_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця дарувальників
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gifters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user_id TEXT UNIQUE NOT NULL,
                    profile_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Індекси для швидкого пошуку
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mentors_user_id 
                ON mentors(user_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mentors_activation_code 
                ON mentors(activation_code)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_streamers_user_id 
                ON streamers(user_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_streamers_created_at 
                ON streamers(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_streamers_mentor_name 
                ON streamers(mentor_name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_gifters_user_id 
                ON gifters(user_id)
            ''')
            
            logging.info("Database initialized successfully")
    
    def add_streamer(self, name: str, user_id: str, profile_url: str, 
                        tg_name: Optional[str] = None, tg_url: Optional[str] = None,
                        instagram_url: Optional[str] = None, platform: Optional[str] = None,
                        mentor_name: Optional[str] = None) -> bool:
        """Додавання або оновлення стрімера"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Перевіряємо чи існує
                cursor.execute('SELECT id FROM streamers WHERE user_id = ?', (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Оновлюємо існуючого (не змінюємо created_at!)
                    cursor.execute('''
                        UPDATE streamers 
                        SET name = ?, 
                            profile_url = ?,
                            tg_name = COALESCE(?, tg_name),
                            tg_url = COALESCE(?, tg_url),
                            instagram_url = COALESCE(?, instagram_url),
                            platform = COALESCE(?, platform),
                            mentor_name = COALESCE(?, mentor_name),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (name, profile_url, tg_name, tg_url, instagram_url, platform, mentor_name, user_id))
                else:
                    # Додаємо нового
                    cursor.execute('''
                        INSERT INTO streamers 
                        (name, user_id, profile_url, tg_name, tg_url, instagram_url, platform, mentor_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, user_id, profile_url, tg_name, tg_url, instagram_url, platform, mentor_name))
                
                return True
        except Exception as e:
            logging.error(f"Error adding streamer: {e}")
            return False
    
    def get_all_streamers(self) -> List[Tuple]:
        """Отримання всіх стрімерів"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    ORDER BY created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting streamers: {e}")
            return []
    
    def get_streamers_by_month(self, year: int, month: int) -> List[Tuple]:
        """Отримання стрімерів за конкретним місяцем та роком"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Виправлено: використовуємо числовий формат для правильного порівняння
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ? 
                        AND CAST(strftime('%m', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (year, month))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting streamers by month: {e}")
            return []
    
    def get_streamers_by_year(self, year: int) -> List[Tuple]:
        """Отримання стрімерів за роком"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE strftime('%Y', created_at) = ?
                    ORDER BY created_at DESC
                ''', (str(year),))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting streamers by year: {e}")
            return []
    
    def get_available_years(self) -> List[int]:
        """Отримання списку років, в які були додані стрімери"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT strftime('%Y', created_at) as year
                    FROM streamers
                    WHERE year IS NOT NULL
                    ORDER BY year DESC
                ''')
                return [int(row[0]) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting available years: {e}")
            return []
    
    def get_available_months_for_year(self, year: int) -> List[int]:
        """Отримання списку місяців в конкретному році"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT strftime('%m', created_at) as month
                    FROM streamers
                    WHERE strftime('%Y', created_at) = ?
                    ORDER BY month DESC
                ''', (str(year),))
                return [int(row[0]) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting available months: {e}")
            return []
    
    def get_streamers_count_by_period(self) -> Dict:
        """Статистика по періодах"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT strftime('%Y-%m', created_at) as period, COUNT(*) as count
                    FROM streamers
                    WHERE period IS NOT NULL
                    GROUP BY period
                    ORDER BY period DESC
                ''')
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return {}
    
    def get_streamer_by_id(self, user_id: str) -> Optional[Dict]:
        """Отримання стрімера за ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'name': row[0],
                        'user_id': row[1],
                        'profile_url': row[2],
                        'tg_name': row[3],
                        'tg_url': row[4],
                        'instagram_url': row[5],
                        'platform': row[6],
                        'mentor_name': row[7],
                        'created_at': row[8]
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting streamer by id: {e}")
            return None
    
    def remove_streamer(self, user_id: str) -> bool:
        """Видалення стрімера"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM streamers WHERE user_id = ?', (user_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error removing streamer: {e}")
            return False
    
    # Методи для дарувальників
    def add_gifter(self, name: str, user_id: str, profile_url: str) -> bool:
        """Додавання дарувальника"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO gifters (name, user_id, profile_url)
                    VALUES (?, ?, ?)
                ''', (name, user_id, profile_url))
                return True
        except sqlite3.IntegrityError:
            # Дарувальник вже існує
            logging.info(f"Gifter {user_id} already exists")
            return False
        except Exception as e:
            logging.error(f"Error adding gifter: {e}")
            return False
    
    def get_all_gifters(self) -> List[Tuple]:
        """Отримання всіх дарувальників"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url
                    FROM gifters
                    ORDER BY created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting gifters: {e}")
            return []
    
    def remove_gifter(self, user_id: str) -> bool:
        """Видалення дарувальника"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM gifters WHERE user_id = ?', (user_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error removing gifter: {e}")
            return False
    
    # Утиліти
    def get_database_stats(self) -> Dict:
        """Отримати загальну статистику БД"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM streamers')
                streamers_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM gifters')
                gifters_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT created_at FROM streamers ORDER BY created_at ASC LIMIT 1')
                first_streamer = cursor.fetchone()
                
                cursor.execute('SELECT created_at FROM streamers ORDER BY created_at DESC LIMIT 1')
                last_streamer = cursor.fetchone()
                
                return {
                    'streamers_count': streamers_count,
                    'gifters_count': gifters_count,
                    'first_streamer_date': first_streamer[0] if first_streamer else None,
                    'last_streamer_date': last_streamer[0] if last_streamer else None
                }
        except Exception as e:
            logging.error(f"Error getting database stats: {e}")
            return {}
    
    def vacuum(self):
        """Оптимізація бази даних"""
        try:
            with self.get_connection() as conn:
                conn.execute('VACUUM')
                logging.info("Database vacuumed successfully")
        except Exception as e:
            logging.error(f"Error vacuuming database: {e}")
    
    # ==================== МЕТОДИ ДЛЯ МЕНТОРІВ ====================
    
    def add_mentor(self, mentor_name: str, user_id: str, profile_url: str,
                    telegram_username: Optional[str] = None, 
                    instagram_url: Optional[str] = None) -> bool:
        """Додавання або оновлення ментора"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT id FROM mentors WHERE user_id = ?', (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE mentors 
                        SET mentor_name = ?,
                            profile_url = ?,
                            telegram_username = COALESCE(?, telegram_username),
                            instagram_url = COALESCE(?, instagram_url),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (mentor_name, profile_url, telegram_username, instagram_url, user_id))
                else:
                    cursor.execute('''
                        INSERT INTO mentors 
                        (mentor_name, user_id, profile_url, telegram_username, instagram_url)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (mentor_name, user_id, profile_url, telegram_username, instagram_url))
                
                return True
        except Exception as e:
            logging.error(f"Error adding mentor: {e}")
            return False
    
    def get_all_mentors(self, sort_by_assignment: bool = False) -> List[Tuple]:
        """Отримання всіх менторів"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if sort_by_assignment:
                    # Сортування за датою останнього призначення (давніші першими)
                    cursor.execute('''
                        SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                                telegram_chat_id, instagram_url, activation_code,
                                last_assigned_at, created_at
                        FROM mentors
                        ORDER BY 
                            CASE WHEN last_assigned_at IS NULL THEN 0 ELSE 1 END,
                            last_assigned_at ASC,
                            created_at ASC
                    ''')
                else:
                    cursor.execute('''
                        SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                                telegram_chat_id, instagram_url, activation_code,
                                last_assigned_at, created_at
                        FROM mentors
                        ORDER BY created_at DESC
                    ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting mentors: {e}")
            return []
    
    def get_mentor_by_id(self, mentor_id: int) -> Optional[Dict]:
        """Отримання ментора за ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                            telegram_chat_id, instagram_url, activation_code,
                            last_assigned_at, created_at
                    FROM mentors
                    WHERE id = ?
                ''', (mentor_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'mentor_name': row[1],
                        'user_id': row[2],
                        'profile_url': row[3],
                        'telegram_username': row[4],
                        'telegram_chat_id': row[5],
                        'instagram_url': row[6],
                        'activation_code': row[7],
                        'last_assigned_at': row[8],
                        'created_at': row[9]
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting mentor by id: {e}")
            return None
    
    def get_mentor_by_user_id(self, user_id: str) -> Optional[Dict]:
        """Отримання ментора за Tango user_id"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                            telegram_chat_id, instagram_url, activation_code,
                            last_assigned_at, created_at
                    FROM mentors
                    WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'mentor_name': row[1],
                        'user_id': row[2],
                        'profile_url': row[3],
                        'telegram_username': row[4],
                        'telegram_chat_id': row[5],
                        'instagram_url': row[6],
                        'activation_code': row[7],
                        'last_assigned_at': row[8],
                        'created_at': row[9]
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting mentor by user_id: {e}")
            return None
    
    def get_mentor_by_activation_code(self, activation_code: str) -> Optional[Dict]:
        """Отримання ментора за кодом активації"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                            telegram_chat_id, instagram_url, activation_code,
                            last_assigned_at, created_at
                    FROM mentors
                    WHERE activation_code = ?
                ''', (activation_code,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'mentor_name': row[1],
                        'user_id': row[2],
                        'profile_url': row[3],
                        'telegram_username': row[4],
                        'telegram_chat_id': row[5],
                        'instagram_url': row[6],
                        'activation_code': row[7],
                        'last_assigned_at': row[8],
                        'created_at': row[9]
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting mentor by activation code: {e}")
            return None
    
    def generate_activation_code(self, mentor_id: int) -> Optional[str]:
        """Генерація коду активації для ментора"""
        import secrets
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                activation_code = secrets.token_urlsafe(16)
                
                cursor.execute('''
                    UPDATE mentors 
                    SET activation_code = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (activation_code, mentor_id))
                
                return activation_code
        except Exception as e:
            logging.error(f"Error generating activation code: {e}")
            return None
    
    def activate_mentor(self, activation_code: str, telegram_chat_id: int) -> bool:
        """Активація ментора через код"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE mentors 
                    SET telegram_chat_id = ?,
                        activation_code = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE activation_code = ?
                ''', (telegram_chat_id, activation_code))
                
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error activating mentor: {e}")
            return False
    
    def update_mentor_last_assigned(self, mentor_name: str) -> bool:
        """Оновлення дати останнього призначення"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE mentors 
                    SET last_assigned_at = CURRENT_TIMESTAMP
                    WHERE mentor_name = ?
                ''', (mentor_name,))
                
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating mentor last assigned: {e}")
            return False
    
    def delete_mentor(self, mentor_id: int) -> bool:
        """Видалення ментора (переміщення в deleted_mentors)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Отримуємо дані ментора
                cursor.execute('''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                            telegram_chat_id, instagram_url, last_assigned_at, created_at
                    FROM mentors
                    WHERE id = ?
                ''', (mentor_id,))
                mentor = cursor.fetchone()
                
                if not mentor:
                    return False
                
                # Копіюємо в deleted_mentors
                cursor.execute('''
                    INSERT INTO deleted_mentors 
                    (id, mentor_name, user_id, profile_url, telegram_username, 
                        telegram_chat_id, instagram_url, last_assigned_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', mentor)
                
                # Видаляємо з mentors
                cursor.execute('DELETE FROM mentors WHERE id = ?', (mentor_id,))
                
                return True
        except Exception as e:
            logging.error(f"Error deleting mentor: {e}")
            return False
    
    def get_deleted_mentors(self) -> List[Tuple]:
        """Отримання видалених менторів"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                            instagram_url, deleted_at
                    FROM deleted_mentors
                    ORDER BY deleted_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting deleted mentors: {e}")
            return []
    
    def restore_mentor(self, mentor_id: int) -> bool:
        """Відновлення ментора з deleted_mentors"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Отримуємо дані видаленого ментора
                cursor.execute('''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username, 
                            telegram_chat_id, instagram_url, last_assigned_at, created_at
                    FROM deleted_mentors
                    WHERE id = ?
                ''', (mentor_id,))
                mentor = cursor.fetchone()
                
                if not mentor:
                    return False
                
                # Відновлюємо в mentors зі старим ID
                cursor.execute('''
                    INSERT INTO mentors 
                    (id, mentor_name, user_id, profile_url, telegram_username, 
                        telegram_chat_id, instagram_url, last_assigned_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', mentor)
                
                # Видаляємо з deleted_mentors
                cursor.execute('DELETE FROM deleted_mentors WHERE id = ?', (mentor_id,))
                
                return True
        except Exception as e:
            logging.error(f"Error restoring mentor: {e}")
            return False
    
    def get_streamers_by_mentor(self, mentor_name: str) -> List[Tuple]:
        """Отримання стрімерів за ментором"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE mentor_name = ?
                    ORDER BY created_at DESC
                ''', (mentor_name,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting streamers by mentor: {e}")
            return []
    
    def get_mentor_statistics(self) -> Dict:
        """Отримання статистики по менторах"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Кількість стрімерів у кожного ментора
                cursor.execute('''
                    SELECT m.id, m.mentor_name, COUNT(s.id) as streamer_count,
                            m.last_assigned_at, m.telegram_chat_id
                    FROM mentors m
                    LEFT JOIN streamers s ON s.mentor_name = m.mentor_name
                    GROUP BY m.id
                    ORDER BY streamer_count ASC, m.last_assigned_at ASC
                ''')
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[1]] = {
                        'id': row[0],
                        'count': row[2],
                        'last_assigned': row[3],
                        'is_activated': row[4] is not None
                    }
                
                # Стрімери без ментора
                cursor.execute('''
                    SELECT COUNT(*) FROM streamers 
                    WHERE mentor_name IS NULL OR mentor_name = ""
                ''')
                stats['Без ментора'] = {
                    'id': None,
                    'count': cursor.fetchone()[0],
                    'last_assigned': None,
                    'is_activated': False
                }
                
                return stats
        except Exception as e:
            logging.error(f"Error getting mentor statistics: {e}")
            return {}
    # def get_streamers_by_mentor(self, mentor_name: str) -> List[Tuple]:
    #     """Отримання стрімерів за ментором"""
    #     try:
    #         with self.get_connection() as conn:
    #             cursor = conn.cursor()
    #             cursor.execute('''
    #                 SELECT name, user_id, profile_url, tg_name, tg_url, 
    #                         instagram_url, platform, mentor_name, created_at
    #                 FROM streamers
    #                 WHERE mentor_name = ?
    #                 ORDER BY created_at DESC
    #             ''', (mentor_name,))
    #             return cursor.fetchall()
    #     except Exception as e:
    #         logging.error(f"Error getting streamers by mentor: {e}")
    #         return []

    def get_streamers_by_mentor_and_year(self, mentor_name: str, year: int) -> List[Tuple]:
        """Отримання стрімерів за ментором та роком"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE mentor_name = ? AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (mentor_name, year))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting streamers by mentor and year: {e}")
            return []

    def get_streamers_by_mentor_and_month(self, mentor_name: str, year: int, month: int) -> List[Tuple]:
        """Отримання стрімерів за ментором та місяцем"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE mentor_name = ? 
                        AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
                        AND CAST(strftime('%m', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (mentor_name, year, month))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting streamers by mentor and month: {e}")
            return []

    def get_mentors_with_streamers(self) -> List[Tuple]:
        """Отримання менторів які мають стрімерів з кількістю"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT mentor_name, COUNT(*) as count
                    FROM streamers
                    WHERE mentor_name IS NOT NULL AND mentor_name != ''
                    GROUP BY mentor_name
                    ORDER BY count DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting mentors with streamers: {e}")
            return []