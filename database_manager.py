"""
Менеджер бази даних SQLite
"""
import logging
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import DB_NAME


class DatabaseManager:

    def __init__(self, db_file: str = DB_NAME):
        self.db_file = db_file
        self.init_database()

    # ================================================================
    # ПІДКЛЮЧЕННЯ
    # ================================================================

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logging.error(f"Database error: {exc}")
            raise
        finally:
            conn.close()

    # ================================================================
    # ІНІЦІАЛІЗАЦІЯ СХЕМИ
    # ================================================================

    def init_database(self) -> None:
        with self.get_connection() as conn:
            cur = conn.cursor()

            # ── bot_users ─────────────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bot_users (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id      INTEGER UNIQUE,
                    username         TEXT UNIQUE,
                    first_name       TEXT,
                    last_name        TEXT,
                    full_name        TEXT,
                    role             TEXT DEFAULT 'guest',
                    status           TEXT DEFAULT 'inactive',
                    activation_code  TEXT UNIQUE,
                    added_by         INTEGER,
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── mentors ───────────────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS mentors (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    mentor_name      TEXT NOT NULL,
                    user_id          TEXT UNIQUE NOT NULL,
                    profile_url      TEXT NOT NULL,
                    telegram_username TEXT,
                    telegram_chat_id INTEGER,
                    instagram_url    TEXT,
                    activation_code  TEXT UNIQUE,
                    last_assigned_at TIMESTAMP,
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── deleted_mentors ───────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS deleted_mentors (
                    id               INTEGER PRIMARY KEY,
                    mentor_name      TEXT NOT NULL,
                    user_id          TEXT NOT NULL,
                    profile_url      TEXT NOT NULL,
                    telegram_username TEXT,
                    telegram_chat_id INTEGER,
                    instagram_url    TEXT,
                    last_assigned_at TIMESTAMP,
                    created_at       TIMESTAMP,
                    deleted_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── streamers ─────────────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS streamers (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name                    TEXT NOT NULL,
                    user_id                 TEXT UNIQUE NOT NULL,
                    profile_url             TEXT NOT NULL,
                    tg_name                 TEXT,
                    tg_url                  TEXT,
                    instagram_url           TEXT,
                    platform                TEXT,
                    mentor_name             TEXT,
                    diamonds_now            INTEGER DEFAULT 0,
                    diamonds_current_month  INTEGER DEFAULT 0,
                    diamonds_previous_month INTEGER DEFAULT 0,
                    diamonds_diff           INTEGER DEFAULT 0,
                    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── gifters ───────────────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS gifters (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    user_id     TEXT NOT NULL,
                    profile_url TEXT NOT NULL,
                    owner_id    INTEGER NOT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, owner_id)
                )
            ''')

            # ── user_donors ───────────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_donors (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER NOT NULL,
                    donor_name      TEXT NOT NULL,
                    donor_tango_id  TEXT NOT NULL,
                    profile_link    TEXT,
                    notes           TEXT,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_telegram_id, donor_tango_id)
                )
            ''')

            # ── audit_log ─────────────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER,
                    user_name        TEXT,
                    action_type      TEXT NOT NULL,
                    target_type      TEXT,
                    target_id        TEXT,
                    target_name      TEXT,
                    details          TEXT,
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── user_activation_codes ─────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_activation_codes (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    activation_code TEXT UNIQUE NOT NULL,
                    role            TEXT NOT NULL,
                    created_by      INTEGER NOT NULL,
                    expires_at      TIMESTAMP NOT NULL,
                    is_used         INTEGER DEFAULT 0,
                    used_by         INTEGER,
                    used_at         TIMESTAMP,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── system_settings ───────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key        TEXT PRIMARY KEY,
                    value      TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── diamonds_errors ───────────────────────────────────
            cur.execute('''
                CREATE TABLE IF NOT EXISTS diamonds_errors (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    streamer_id   TEXT NOT NULL,
                    streamer_name TEXT,
                    error_text    TEXT,
                    retries       INTEGER DEFAULT 0,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ── індекси ───────────────────────────────────────────
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_bot_users_telegram_id ON bot_users(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_mentors_user_id ON mentors(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_mentors_activation_code ON mentors(activation_code)",
                "CREATE INDEX IF NOT EXISTS idx_streamers_user_id ON streamers(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_streamers_created_at ON streamers(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_streamers_mentor_name ON streamers(mentor_name)",
                "CREATE INDEX IF NOT EXISTS idx_gifters_user_id ON gifters(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_gifters_owner_id ON gifters(owner_id)",
            ]
            for sql in indexes:
                cur.execute(sql)

            logging.info("Database initialized successfully")

    # ================================================================
    # SYSTEM SETTINGS
    # ================================================================

    def get_setting(self, key: str) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT value FROM system_settings WHERE key = ?', (key,)
                ).fetchone()
                return row['value'] if row else None
        except Exception as exc:
            logging.error(f"get_setting {key}: {exc}")
            return None

    def set_setting(self, key: str, value: str) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO system_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                ''', (key, value))
        except Exception as exc:
            logging.error(f"set_setting {key}: {exc}")

    # ================================================================
    # BOT USERS
    # ================================================================

    def get_user_role(self, telegram_id: int) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT role FROM bot_users WHERE telegram_id = ?', (telegram_id,)
                ).fetchone()
                return row['role'] if row else None
        except Exception as exc:
            logging.error(f"get_user_role: {exc}")
            return None

    def add_bot_user(
        self, telegram_id: int, username: Optional[str], role: str, added_by: int,
        first_name: Optional[str] = None, last_name: Optional[str] = None,
        status: str = 'active'
    ) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO bot_users
                        (telegram_id, username, first_name, last_name, role, status, added_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (telegram_id, username, first_name, last_name, role, status, added_by))
                return True
        except Exception as exc:
            logging.error(f"add_bot_user: {exc}")
            return False

    def add_bot_user_pending(
        self, username: str, role: str, added_by: int, activation_code: str
    ) -> bool:
        try:
            with self.get_connection() as conn:
                existing = conn.execute(
                    'SELECT id FROM bot_users WHERE LOWER(username) = LOWER(?)', (username,)
                ).fetchone()
                if existing:
                    logging.warning(f"Bot user '{username}' already exists")
                    return False
                conn.execute('''
                    INSERT INTO bot_users (username, role, status, activation_code, added_by)
                    VALUES (?, ?, 'pending', ?, ?)
                ''', (username, role, activation_code, added_by))
                return True
        except Exception as exc:
            logging.error(f"add_bot_user_pending: {exc}")
            return False

    def add_bot_user_by_username(
        self, username: str, role: str, added_by: int, status: str = 'inactive'
    ) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO bot_users (username, role, status, added_by)
                    VALUES (?, ?, ?, ?)
                ''', (username, role, status, added_by))
                return True
        except Exception as exc:
            logging.error(f"add_bot_user_by_username: {exc}")
            return False

    def activate_bot_user(self, activation_code: str, telegram_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE bot_users
                    SET status = 'active', telegram_id = ?,
                        activation_code = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE activation_code = ?
                ''', (telegram_id, activation_code))
                return True
        except Exception as exc:
            logging.error(f"activate_bot_user: {exc}")
            return False

    def _hydrate_user(self, row) -> Dict:
        """Додає full_name до словника користувача"""
        d = dict(row)
        if not d.get('full_name'):
            parts = [p for p in [d.get('first_name'), d.get('last_name')] if p]
            d['full_name'] = ' '.join(parts) or None
        return d

    def get_bot_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    '''SELECT telegram_id, username, first_name, last_name, full_name,
                              role, status, added_by, created_at
                       FROM bot_users WHERE telegram_id = ?''',
                    (telegram_id,)
                ).fetchone()
                return self._hydrate_user(row) if row else None
        except Exception as exc:
            logging.error(f"get_bot_user_by_telegram_id: {exc}")
            return None

    # ── Аліаси для сумісності зі старим кодом ────────────────────

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Аліас → get_bot_user_by_telegram_id"""
        return self.get_bot_user_by_telegram_id(telegram_id)

    def add_user(
        self, telegram_id: int, username: str, full_name: str,
        role: str, created_by: int, status: str = 'active'
    ) -> Optional[int]:
        """
        Аліас для user_handlers.py.
        Приймає full_name як єдине поле.
        Повертає telegram_id при успіху або None.
        """
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    INSERT OR REPLACE INTO bot_users
                        (telegram_id, username, full_name, first_name, role, status, added_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (telegram_id, username or None, full_name, full_name, role, status, created_by))
                return telegram_id if cur.rowcount else None
        except Exception as exc:
            logging.error(f"add_user: {exc}")
            return None

    def delete_user(self, telegram_id: int) -> bool:
        """Аліас → delete_bot_user"""
        return self.delete_bot_user(telegram_id)

    def update_user_role(self, telegram_id: int, new_role: str) -> bool:
        """Аліас → update_bot_user_role"""
        return self.update_bot_user_role(telegram_id, new_role)

    def get_all_users(self, role: Optional[str] = None) -> List[Dict]:
        """
        Аліас для user_handlers / stats_handlers.
        Повертає список dict з full_name.
        """
        try:
            with self.get_connection() as conn:
                if role:
                    rows = conn.execute(
                        '''SELECT telegram_id, username, first_name, last_name, full_name,
                                  role, status, created_at
                           FROM bot_users WHERE role = ? ORDER BY created_at DESC''',
                        (role,)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        '''SELECT telegram_id, username, first_name, last_name, full_name,
                                  role, status, created_at
                           FROM bot_users ORDER BY created_at DESC'''
                    ).fetchall()
                return [self._hydrate_user(r) for r in rows]
        except Exception as exc:
            logging.error(f"get_all_users: {exc}")
            return []

    def get_bot_user_by_username(self, username: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    '''SELECT telegram_id, username, first_name, last_name, full_name,
                              role, status, added_by, created_at
                       FROM bot_users WHERE LOWER(username) = LOWER(?)''',
                    (username,)
                ).fetchone()
                return self._hydrate_user(row) if row else None
        except Exception as exc:
            logging.error(f"get_bot_user_by_username: {exc}")
            return None

    def get_all_bot_users(self) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute(
                    'SELECT telegram_id, username, role, status, created_at '
                    'FROM bot_users ORDER BY created_at DESC'
                )
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_all_bot_users: {exc}")
            return []

    def update_bot_user_role(self, telegram_id: int, new_role: str) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE bot_users SET role = ?, updated_at = CURRENT_TIMESTAMP '
                    'WHERE telegram_id = ?',
                    (new_role, telegram_id)
                )
                return True
        except Exception as exc:
            logging.error(f"update_bot_user_role: {exc}")
            return False

    def update_bot_user_role_by_username(self, username: str, new_role: str) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'UPDATE bot_users SET role = ?, updated_at = CURRENT_TIMESTAMP '
                    'WHERE username = ?',
                    (new_role, username)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"update_bot_user_role_by_username: {exc}")
            return False

    def deactivate_bot_user(self, telegram_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    "UPDATE bot_users SET status = 'inactive', updated_at = CURRENT_TIMESTAMP "
                    "WHERE telegram_id = ?",
                    (telegram_id,)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"deactivate_bot_user: {exc}")
            return False

    def delete_bot_user(self, telegram_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'DELETE FROM bot_users WHERE telegram_id = ?', (telegram_id,)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"delete_bot_user: {exc}")
            return False

    def delete_bot_user_by_username(self, username: str) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'DELETE FROM bot_users WHERE username = ?', (username,)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"delete_bot_user_by_username: {exc}")
            return False

    def get_admin_and_owner_ids(self) -> List[int]:
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT telegram_id FROM bot_users "
                    "WHERE role IN ('owner','superadmin','admin') "
                    "AND status = 'active' AND telegram_id IS NOT NULL"
                ).fetchall()
                return [r['telegram_id'] for r in rows]
        except Exception as exc:
            logging.error(f"get_admin_and_owner_ids: {exc}")
            return []

    # ── Коди активації користувачів ───────────────────────────────

    def create_user_activation_code(
        self, role: str, created_by: int, hours_valid: int = 24
    ) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                code = secrets.token_urlsafe(12)
                expires_at = datetime.now() + timedelta(hours=hours_valid)
                conn.execute('''
                    INSERT INTO user_activation_codes
                        (activation_code, role, created_by, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (code, role, created_by, expires_at.isoformat()))
                return code
        except Exception as exc:
            logging.error(f"create_user_activation_code: {exc}")
            return None

    def get_activation_code_info(self, activation_code: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    '''SELECT id, activation_code, role, created_by, expires_at,
                              is_used, used_by, used_at
                       FROM user_activation_codes WHERE activation_code = ?''',
                    (activation_code,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logging.error(f"get_activation_code_info: {exc}")
            return None

    def use_activation_code(self, activation_code: str, telegram_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    UPDATE user_activation_codes
                    SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP
                    WHERE activation_code = ? AND is_used = 0
                ''', (telegram_id, activation_code))
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"use_activation_code: {exc}")
            return False

    def delete_expired_activation_codes(self) -> None:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    "DELETE FROM user_activation_codes "
                    "WHERE expires_at < ? AND is_used = 0",
                    (datetime.now().isoformat(),)
                )
                if cur.rowcount:
                    logging.info(f"Deleted {cur.rowcount} expired activation codes")
        except Exception as exc:
            logging.error(f"delete_expired_activation_codes: {exc}")

    # ================================================================
    # STREAMERS
    # ================================================================

    def add_streamer(
        self, name: str, user_id: str, profile_url: str,
        tg_name: Optional[str] = None, tg_url: Optional[str] = None,
        instagram_url: Optional[str] = None, platform: Optional[str] = None,
        mentor_name: Optional[str] = None
    ) -> bool:
        try:
            with self.get_connection() as conn:
                existing = conn.execute(
                    'SELECT id FROM streamers WHERE user_id = ?', (user_id,)
                ).fetchone()
                if existing:
                    conn.execute('''
                        UPDATE streamers
                        SET name        = ?,
                            profile_url = ?,
                            tg_name     = COALESCE(?, tg_name),
                            tg_url      = COALESCE(?, tg_url),
                            instagram_url = COALESCE(?, instagram_url),
                            platform    = COALESCE(?, platform),
                            mentor_name = COALESCE(?, mentor_name),
                            updated_at  = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (name, profile_url, tg_name, tg_url,
                          instagram_url, platform, mentor_name, user_id))
                else:
                    conn.execute('''
                        INSERT INTO streamers
                            (name, user_id, profile_url, tg_name, tg_url,
                             instagram_url, platform, mentor_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, user_id, profile_url, tg_name, tg_url,
                          instagram_url, platform, mentor_name))
                return True
        except Exception as exc:
            logging.error(f"add_streamer: {exc}")
            return False

    def get_streamer_by_id(self, user_id: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM streamers WHERE user_id = ?', (user_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logging.error(f"get_streamer_by_id: {exc}")
            return None

    def get_all_streamers(self) -> List[Tuple]:
        """Для сумісності з існуючими handlers (повертає tuples)"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers ORDER BY created_at DESC
                ''')
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_all_streamers: {exc}")
            return []

    def get_all_streamers_full(self) -> List[Dict]:
        """Всі поля для Google Sheets"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM streamers ORDER BY created_at DESC'
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as exc:
            logging.error(f"get_all_streamers_full: {exc}")
            return []

    def get_all_streamers_for_diamonds(self) -> List[Dict]:
        """Для diamonds_service"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT user_id, name,
                           diamonds_now, diamonds_current_month,
                           diamonds_previous_month, diamonds_diff
                    FROM streamers ORDER BY name ASC
                ''').fetchall()
                return [dict(r) for r in rows]
        except Exception as exc:
            logging.error(f"get_all_streamers_for_diamonds: {exc}")
            return []

    def get_streamers_count_by_period(self) -> dict:
        """Повертає {\'YYYY-MM\': count} для статистики"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT strftime(\'%Y-%m\', created_at) AS period, COUNT(*) AS cnt
                    FROM streamers
                    GROUP BY period
                    ORDER BY period DESC
                ''').fetchall()
                return {r['period']: r['cnt'] for r in rows}
        except Exception as exc:
            logging.error(f"get_streamers_count_by_period: {exc}")
            return {}

    def get_available_years(self) -> list:
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT DISTINCT CAST(strftime(\'%Y\', created_at) AS INTEGER) AS yr
                    FROM streamers ORDER BY yr DESC
                ''').fetchall()
                return [r['yr'] for r in rows]
        except Exception as exc:
            logging.error(f"get_available_years: {exc}")
            return []

    def get_available_months_for_year(self, year: int) -> list:
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT DISTINCT CAST(strftime(\'%m\', created_at) AS INTEGER) AS mo
                    FROM streamers
                    WHERE CAST(strftime(\'%Y\', created_at) AS INTEGER) = ?
                    ORDER BY mo
                ''', (year,)).fetchall()
                return [r['mo'] for r in rows]
        except Exception as exc:
            logging.error(f"get_available_months_for_year: {exc}")
            return []

    def update_streamer_field(self, user_id: str, field: str, value) -> bool:
        allowed = {
            'name', 'profile_url', 'tg_name', 'tg_url',
            'instagram_url', 'platform', 'mentor_name'
        }
        if field not in allowed:
            logging.error(f"update_streamer_field: invalid field '{field}'")
            return False
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    f'UPDATE streamers SET {field} = ?, updated_at = CURRENT_TIMESTAMP '
                    f'WHERE user_id = ?',
                    (value, user_id)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"update_streamer_field: {exc}")
            return False

    def delete_streamer(self, user_id: str) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'DELETE FROM streamers WHERE user_id = ?', (user_id,)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"delete_streamer: {exc}")
            return False

    def get_streamers_without_mentor(self) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE mentor_name IS NULL OR mentor_name = ''
                    ORDER BY created_at DESC
                ''')
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_streamers_without_mentor: {exc}")
            return []

    def get_streamers_by_mentor(self, mentor_name_or_id) -> List[Tuple]:
        """
        Приймає mentor_name (str) або mentor_id (int).
        user_handlers.py передає mentor['id'] (int),
        більшість інших хендлерів передають ім'я (str).
        """
        try:
            # Якщо передано int — шукаємо ім'я ментора в таблиці mentors
            if isinstance(mentor_name_or_id, int):
                with self.get_connection() as conn:
                    row = conn.execute(
                        'SELECT mentor_name FROM mentors WHERE id = ?', (mentor_name_or_id,)
                    ).fetchone()
                    if not row:
                        return []
                    mentor_name = row['mentor_name']
            else:
                mentor_name = mentor_name_or_id

            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers WHERE mentor_name = ?
                    ORDER BY created_at DESC
                ''', (mentor_name,))
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_streamers_by_mentor: {exc}")
            return []

    def get_streamers_by_year(self, year: int) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (year,))
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_streamers_by_year: {exc}")
            return []

    def get_streamers_by_month(self, year: int, month: int) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE CAST(strftime('%Y', created_at) AS INTEGER) = ?
                      AND CAST(strftime('%m', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (year, month))
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_streamers_by_month: {exc}")
            return []

    def get_streamers_by_mentor_and_year(self, mentor_name: str, year: int) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE mentor_name = ?
                      AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (mentor_name, year))
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_streamers_by_mentor_and_year: {exc}")
            return []

    def get_streamers_by_mentor_and_month(
        self, mentor_name: str, year: int, month: int
    ) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT name, user_id, profile_url, tg_name, tg_url,
                           instagram_url, platform, mentor_name, created_at
                    FROM streamers
                    WHERE mentor_name = ?
                      AND CAST(strftime('%Y', created_at) AS INTEGER) = ?
                      AND CAST(strftime('%m', created_at) AS INTEGER) = ?
                    ORDER BY created_at DESC
                ''', (mentor_name, year, month))
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_streamers_by_mentor_and_month: {exc}")
            return []

    def get_mentors_with_streamers(self) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT mentor_name, COUNT(*) AS count
                    FROM streamers
                    WHERE mentor_name IS NOT NULL AND mentor_name != ''
                    GROUP BY mentor_name ORDER BY count DESC
                ''')
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_mentors_with_streamers: {exc}")
            return []

    # ── Діаманти ──────────────────────────────────────────────────

    def update_streamer_diamonds_now(self, user_id: str, diamonds: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'UPDATE streamers SET diamonds_now = ?, updated_at = CURRENT_TIMESTAMP '
                    'WHERE user_id = ?',
                    (diamonds, user_id)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"update_streamer_diamonds_now: {exc}")
            return False

    def monthly_rotate_diamonds(
        self, user_id: str, old_current: int, new_current: int, diff: int
    ) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    UPDATE streamers
                    SET diamonds_previous_month = ?,
                        diamonds_current_month  = ?,
                        diamonds_diff           = ?,
                        diamonds_now            = ?,
                        updated_at              = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (old_current, new_current, diff, new_current, user_id))
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"monthly_rotate_diamonds: {exc}")
            return False

    def monthly_rotate_diamonds_deleted(self, user_id: str, old_current: int) -> bool:
        """Стрімер недоступний — позначаємо current = -1"""
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    UPDATE streamers
                    SET diamonds_previous_month = ?,
                        diamonds_current_month  = -1,
                        diamonds_diff           = 0,
                        updated_at              = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (old_current, user_id))
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"monthly_rotate_diamonds_deleted: {exc}")
            return False

    def get_diamonds_summary(self) -> Dict:
        try:
            with self.get_connection() as conn:
                row = conn.execute('''
                    SELECT COUNT(*) AS total_streamers,
                           SUM(CASE WHEN diamonds_now  > 0 THEN diamonds_now  ELSE 0 END) AS total_now,
                           SUM(CASE WHEN diamonds_diff > 0 THEN diamonds_diff ELSE 0 END) AS total_diff
                    FROM streamers
                ''').fetchone()
                return {
                    'total_streamers': row['total_streamers'] or 0,
                    'total_now':       row['total_now']       or 0,
                    'total_diff':      row['total_diff']      or 0,
                }
        except Exception as exc:
            logging.error(f"get_diamonds_summary: {exc}")
            return {'total_streamers': 0, 'total_now': 0, 'total_diff': 0}

    # ── diamonds_errors ───────────────────────────────────────────

    def log_diamonds_error(
        self, streamer_id: str, streamer_name: str, error_text: str, retries: int
    ) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO diamonds_errors
                        (streamer_id, streamer_name, error_text, retries)
                    VALUES (?, ?, ?, ?)
                ''', (streamer_id, streamer_name, error_text, retries))
        except Exception as exc:
            logging.error(f"log_diamonds_error: {exc}")

    def get_diamonds_errors(self, limit: int = 200) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT streamer_id, streamer_name, error_text, retries, created_at
                    FROM diamonds_errors ORDER BY created_at DESC LIMIT ?
                ''', (limit,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as exc:
            logging.error(f"get_diamonds_errors: {exc}")
            return []

    # ================================================================
    # MENTORS
    # ================================================================

    def add_mentor(
        self, mentor_name: str, user_id: str, profile_url: str,
        telegram_username: Optional[str] = None,
        instagram_url: Optional[str] = None
    ) -> bool:
        try:
            with self.get_connection() as conn:
                existing = conn.execute(
                    'SELECT id FROM mentors WHERE user_id = ?', (user_id,)
                ).fetchone()
                if existing:
                    conn.execute('''
                        UPDATE mentors
                        SET mentor_name       = ?,
                            profile_url       = ?,
                            telegram_username = ?,
                            instagram_url     = ?,
                            updated_at        = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (mentor_name, profile_url, telegram_username, instagram_url, user_id))
                else:
                    conn.execute('''
                        INSERT INTO mentors
                            (mentor_name, user_id, profile_url, telegram_username, instagram_url)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (mentor_name, user_id, profile_url, telegram_username, instagram_url))
                return True
        except Exception as exc:
            logging.error(f"add_mentor: {exc}")
            return False

    def get_mentor_by_id(self, mentor_id: int) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM mentors WHERE id = ?', (mentor_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logging.error(f"get_mentor_by_id: {exc}")
            return None

    def get_mentor_by_user_id(self, user_id: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM mentors WHERE user_id = ?', (user_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logging.error(f"get_mentor_by_user_id: {exc}")
            return None

    def get_mentor_by_telegram_id(self, telegram_chat_id: int) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM mentors WHERE telegram_chat_id = ?', (telegram_chat_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logging.error(f"get_mentor_by_telegram_id: {exc}")
            return None

    def get_mentor_by_activation_code(self, activation_code: str) -> Optional[Dict]:
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM mentors WHERE activation_code = ?', (activation_code,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logging.error(f"get_mentor_by_activation_code: {exc}")
            return None

    def get_all_mentors(self, sort_by_assignment: bool = False) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                order = (
                    'ORDER BY CASE WHEN last_assigned_at IS NULL THEN 0 ELSE 1 END, '
                    'last_assigned_at ASC, created_at ASC'
                    if sort_by_assignment
                    else 'ORDER BY created_at DESC'
                )
                cur.execute(f'''
                    SELECT id, mentor_name, user_id, profile_url, telegram_username,
                           telegram_chat_id, instagram_url, activation_code,
                           last_assigned_at, created_at
                    FROM mentors {order}
                ''')
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_all_mentors: {exc}")
            return []

    def get_deleted_mentors(self) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                cur.execute('''
                    SELECT id, mentor_name, user_id, profile_url,
                           telegram_username, instagram_url, deleted_at
                    FROM deleted_mentors ORDER BY deleted_at DESC
                ''')
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_deleted_mentors: {exc}")
            return []

    def get_mentor_statistics(self) -> Dict:
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT m.mentor_name,
                           COUNT(s.id) AS count,
                           MAX(s.created_at) AS last_assigned,
                           CASE WHEN m.telegram_chat_id IS NOT NULL THEN 1 ELSE 0 END AS is_activated
                    FROM mentors m
                    LEFT JOIN streamers s ON s.mentor_name = m.mentor_name
                    GROUP BY m.id
                ''').fetchall()
                return {
                    r['mentor_name']: {
                        'count':        r['count'],
                        'last_assigned': r['last_assigned'],
                        'is_activated': bool(r['is_activated']),
                    }
                    for r in rows
                }
        except Exception as exc:
            logging.error(f"get_mentor_statistics: {exc}")
            return {}

    def delete_mentor(self, mentor_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                mentor = conn.execute(
                    'SELECT * FROM mentors WHERE id = ?', (mentor_id,)
                ).fetchone()
                if not mentor:
                    return False
                conn.execute('''
                    INSERT INTO deleted_mentors
                        (id, mentor_name, user_id, profile_url, telegram_username,
                         telegram_chat_id, instagram_url, last_assigned_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mentor['id'], mentor['mentor_name'], mentor['user_id'],
                    mentor['profile_url'], mentor['telegram_username'],
                    mentor['telegram_chat_id'], mentor['instagram_url'],
                    mentor['last_assigned_at'], mentor['created_at']
                ))
                conn.execute('DELETE FROM mentors WHERE id = ?', (mentor_id,))
                return True
        except Exception as exc:
            logging.error(f"delete_mentor: {exc}")
            return False

    def restore_mentor(self, mentor_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                deleted = conn.execute(
                    'SELECT * FROM deleted_mentors WHERE id = ?', (mentor_id,)
                ).fetchone()
                if not deleted:
                    return False
                conn.execute('''
                    INSERT OR IGNORE INTO mentors
                        (id, mentor_name, user_id, profile_url, telegram_username,
                         telegram_chat_id, instagram_url, last_assigned_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    deleted['id'], deleted['mentor_name'], deleted['user_id'],
                    deleted['profile_url'], deleted['telegram_username'],
                    deleted['telegram_chat_id'], deleted['instagram_url'],
                    deleted['last_assigned_at'], deleted['created_at']
                ))
                conn.execute('DELETE FROM deleted_mentors WHERE id = ?', (mentor_id,))
                return True
        except Exception as exc:
            logging.error(f"restore_mentor: {exc}")
            return False

    def activate_mentor(self, activation_code: str, telegram_chat_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    UPDATE mentors
                    SET telegram_chat_id = ?, activation_code = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE activation_code = ?
                ''', (telegram_chat_id, activation_code))
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"activate_mentor: {exc}")
            return False

    def generate_activation_code(self, mentor_id: int) -> Optional[str]:
        try:
            with self.get_connection() as conn:
                code = secrets.token_urlsafe(16)
                conn.execute(
                    'UPDATE mentors SET activation_code = ?, updated_at = CURRENT_TIMESTAMP '
                    'WHERE id = ?',
                    (code, mentor_id)
                )
                return code
        except Exception as exc:
            logging.error(f"generate_activation_code: {exc}")
            return None

    def update_mentor_last_assigned(self, mentor_name: str) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE mentors SET last_assigned_at = CURRENT_TIMESTAMP '
                    'WHERE mentor_name = ?',
                    (mentor_name,)
                )
        except Exception as exc:
            logging.error(f"update_mentor_last_assigned: {exc}")

    def update_mentor_field(self, mentor_id: int, field: str, value) -> bool:
        allowed = {
            'telegram_username', 'instagram_url', 'mentor_name',
            'profile_url', 'telegram_chat_id'
        }
        if field not in allowed:
            logging.error(f"update_mentor_field: invalid field '{field}'")
            return False
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    f'UPDATE mentors SET {field} = ?, updated_at = CURRENT_TIMESTAMP '
                    f'WHERE id = ?',
                    (value, mentor_id)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"update_mentor_field: {exc}")
            return False

    def update_mentor_profile(
        self, mentor_id: int, new_name: str, new_user_id: str,
        new_profile_url: str, old_name: str
    ) -> bool:
        """Оновлює профіль ментора і синхронізує mentor_name у всіх стрімерів."""
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    UPDATE mentors
                    SET mentor_name = ?,
                        user_id     = ?,
                        profile_url = ?,
                        updated_at  = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_name, new_user_id, new_profile_url, mentor_id))
                if cur.rowcount == 0:
                    return False
                # Оновлюємо mentor_name у всіх стрімерів
                conn.execute(
                    'UPDATE streamers SET mentor_name = ? WHERE mentor_name = ?',
                    (new_name, old_name)
                )
                return True
        except Exception as exc:
            logging.error(f"update_mentor_profile: {exc}")
            return False

    # ================================================================
    # GIFTERS
    # ================================================================

    def add_gifter(
        self, name: str, user_id: str, profile_url: str, owner_id: int
    ) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO gifters (name, user_id, profile_url, owner_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, user_id, profile_url, owner_id))
                return True
        except sqlite3.IntegrityError:
            logging.info(f"Gifter {user_id} already exists for owner {owner_id}")
            return False
        except Exception as exc:
            logging.error(f"add_gifter: {exc}")
            return False

    def get_all_gifters(self, owner_id: Optional[int] = None) -> List[Tuple]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = None
                cur = conn.cursor()
                if owner_id is None:
                    cur.execute(
                        'SELECT DISTINCT name, user_id, profile_url, owner_id, created_at '
                        'FROM gifters ORDER BY created_at DESC'
                    )
                else:
                    cur.execute(
                        'SELECT name, user_id, profile_url, owner_id, created_at '
                        'FROM gifters WHERE owner_id = ? ORDER BY created_at DESC',
                        (owner_id,)
                    )
                return cur.fetchall()
        except Exception as exc:
            logging.error(f"get_all_gifters: {exc}")
            return []

    def remove_gifter(self, user_id: str, owner_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'DELETE FROM gifters WHERE user_id = ? AND owner_id = ?',
                    (user_id, owner_id)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"remove_gifter: {exc}")
            return False

    # ================================================================
    # USER DONORS (особисті даруваники менторів)
    # ================================================================

    def add_user_donor(
        self, user_telegram_id: int, donor_name: str, donor_tango_id: str,
        profile_link: Optional[str] = None, notes: Optional[str] = None
    ) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''
                    INSERT INTO user_donors
                        (user_telegram_id, donor_name, donor_tango_id, profile_link, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_telegram_id, donor_name, donor_tango_id, profile_link, notes))
                return cur.lastrowid
        except sqlite3.IntegrityError:
            return None
        except Exception as exc:
            logging.error(f"add_user_donor: {exc}")
            return None

    def get_user_donors(self, user_telegram_id: int) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM user_donors WHERE user_telegram_id = ? '
                    'ORDER BY created_at DESC',
                    (user_telegram_id,)
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as exc:
            logging.error(f"get_user_donors: {exc}")
            return []

    def search_user_donor(self, user_telegram_id: int, query: str) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                q = f'%{query}%'
                rows = conn.execute('''
                    SELECT * FROM user_donors
                    WHERE user_telegram_id = ?
                      AND (donor_name LIKE ? OR donor_tango_id LIKE ?)
                    ORDER BY created_at DESC
                ''', (user_telegram_id, q, q)).fetchall()
                return [dict(r) for r in rows]
        except Exception as exc:
            logging.error(f"search_user_donor: {exc}")
            return []

    def delete_user_donor(self, donor_id: int) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    'DELETE FROM user_donors WHERE id = ?', (donor_id,)
                )
                return cur.rowcount > 0
        except Exception as exc:
            logging.error(f"delete_user_donor: {exc}")
            return False

    def get_all_user_donors_grouped(self) -> Dict:
        """Для адміністративного перегляду — згруповано по власнику"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT ud.*, bu.username AS user_name
                    FROM user_donors ud
                    LEFT JOIN bot_users bu ON bu.telegram_id = ud.user_telegram_id
                    ORDER BY ud.user_telegram_id, ud.created_at DESC
                ''').fetchall()
                result: Dict = {}
                for r in rows:
                    d = dict(r)
                    uid = d['user_telegram_id']
                    result.setdefault(uid, []).append(d)
                return result
        except Exception as exc:
            logging.error(f"get_all_user_donors_grouped: {exc}")
            return {}

    # ================================================================
    # AUDIT LOG
    # ================================================================

    def add_audit_log(
        self, user_telegram_id: int, user_name: str, action_type: str,
        target_type: Optional[str] = None, target_id: Optional[str] = None,
        target_name: Optional[str] = None, details: Optional[Dict] = None
    ) -> None:
        import json
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO audit_log
                        (user_telegram_id, user_name, action_type,
                         target_type, target_id, target_name, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_telegram_id, user_name, action_type,
                    target_type, target_id, target_name,
                    json.dumps(details, ensure_ascii=False) if details else None
                ))
        except Exception as exc:
            logging.error(f"add_audit_log: {exc}")

    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as exc:
            logging.error(f"get_audit_logs: {exc}")
            return []

    # ================================================================
    # УТИЛІТИ
    # ================================================================

    def get_database_stats(self) -> Dict:
        try:
            with self.get_connection() as conn:
                return {
                    'streamers_count': conn.execute(
                        'SELECT COUNT(*) FROM streamers'
                    ).fetchone()[0],
                    'gifters_count': conn.execute(
                        'SELECT COUNT(*) FROM gifters'
                    ).fetchone()[0],
                    'mentors_count': conn.execute(
                        'SELECT COUNT(*) FROM mentors'
                    ).fetchone()[0],
                }
        except Exception as exc:
            logging.error(f"get_database_stats: {exc}")
            return {}

    def vacuum(self) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute('VACUUM')
        except Exception as exc:
            logging.error(f"vacuum: {exc}")
