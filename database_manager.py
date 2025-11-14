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
                CREATE INDEX IF NOT EXISTS idx_streamers_user_id 
                ON streamers(user_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_streamers_created_at 
                ON streamers(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_gifters_user_id 
                ON gifters(user_id)
            ''')
            
            logging.info("Database initialized successfully")
    
    def add_streamer(self, name: str, user_id: str, profile_url: str, 
                        tg_name: Optional[str] = None, tg_url: Optional[str] = None,
                        instagram_url: Optional[str] = None, platform: Optional[str] = None) -> bool:
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
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (name, profile_url, tg_name, tg_url, instagram_url, platform, user_id))
                else:
                    # Додаємо нового
                    cursor.execute('''
                        INSERT INTO streamers 
                        (name, user_id, profile_url, tg_name, tg_url, instagram_url, platform)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (name, user_id, profile_url, tg_name, tg_url, instagram_url, platform))
                
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
                            instagram_url, platform, created_at
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
                cursor.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url, 
                            instagram_url, platform, created_at
                    FROM streamers
                    WHERE strftime('%Y', created_at) = ? 
                        AND strftime('%m', created_at) = ?
                    ORDER BY created_at DESC
                ''', (str(year), f'{month:02d}'))
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
                            instagram_url, platform, created_at
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
                            instagram_url, platform, created_at
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
                        'created_at': row[7]
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