"""
Сервіс синхронізації з Google Sheets
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_SHEET_ID,
    GOOGLE_SHEET_NAME,
    OWNER_ID,
    SHEET_ERRORS,
    SHEET_GIFTERS,
    SHEET_MENTORS,
    SHEET_STREAMERS,
    SHEETS_SYNC_INTERVAL,
)

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Заголовки аркушів
HEADERS_STREAMERS = [
    "ID", "Ім'я", "Профіль", "Telegram", "Instagram", "Платформа", "Ментор",
    "Діаманти зараз", "Діаманти поточний місяць",
    "Діаманти попередній місяць", "Різниця за місяць",
    "Дата додавання",
]
HEADERS_MENTORS = [
    "ID", "Ім'я", "Профіль", "Telegram", "Instagram",
    "Активовано", "К-ть стрімерів", "Дата додавання",
]
HEADERS_GIFTERS = [
    "ID", "Ім'я", "Профіль", "Власник (хто додав)", "Дата додавання",
]
HEADERS_ERRORS = [
    "Дата", "Стрімер ID", "Ім'я стрімера", "Помилка", "Спроби",
]


class GoogleSheetsService:
    """Batch-синхронізація бази даних з Google Sheets"""

    def __init__(self, db, bot=None):
        self.db = db
        self.bot = bot
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        self._pending_sync: set = set()   # {'streamers', 'mentors', 'gifters', 'errors'}
        self._sync_task: Optional[asyncio.Task] = None

    # ================================================================
    # ІНІЦІАЛІЗАЦІЯ
    # ================================================================

    def _get_client(self) -> gspread.Client:
        if self._client is None:
            creds = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client

    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            self._spreadsheet = self._get_client().open_by_key(GOOGLE_SHEET_ID)
        return self._spreadsheet

    def _get_or_create_worksheet(self, title: str, headers: list) -> gspread.Worksheet:
        """Отримує аркуш або створює його з заголовками"""
        ss = self._get_spreadsheet()
        try:
            ws = ss.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = ss.add_worksheet(title=title, rows=1000, cols=len(headers))
            ws.append_row(headers, value_input_option='RAW')
            logging.info(f"Створено аркуш '{title}'")
        return ws

    # ================================================================
    # ПУБЛІЧНИЙ ІНТЕРФЕЙС: ПОСТАНОВКА В ЧЕРГУ
    # ================================================================

    def schedule_sync(self, sheet: str) -> None:
        """
        Ставить аркуш у чергу синхронізації.
        sheet: 'streamers' | 'mentors' | 'gifters' | 'errors'
        """
        self._pending_sync.add(sheet)

    def schedule_all(self) -> None:
        self._pending_sync.update({'streamers', 'mentors', 'gifters'})

    # ================================================================
    # ФОНОВИЙ WORKER (запускається при старті бота)
    # ================================================================

    async def start_background_worker(self) -> None:
        """Запускає фоновий цикл синхронізації кожні SHEETS_SYNC_INTERVAL секунд"""
        self._sync_task = asyncio.create_task(self._sync_loop())
        logging.info("Google Sheets background worker запущено")

    async def _sync_loop(self) -> None:
        while True:
            await asyncio.sleep(SHEETS_SYNC_INTERVAL)
            if not self._pending_sync:
                continue
            sheets_to_sync = self._pending_sync.copy()
            self._pending_sync.clear()
            await self._process_sync(sheets_to_sync)

    async def _process_sync(self, sheets: set) -> None:
        for sheet in sheets:
            try:
                if sheet == 'streamers':
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._sync_streamers_sync
                    )
                elif sheet == 'mentors':
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._sync_mentors_sync
                    )
                elif sheet == 'gifters':
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._sync_gifters_sync
                    )
                elif sheet == 'errors':
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._sync_errors_sync
                    )
            except Exception as exc:
                logging.error(f"Sheets sync '{sheet}' failed: {exc}")
                await self._notify_admins_error(sheet, str(exc))

    # ================================================================
    # ПРЯМИЙ ВИКЛИК (для diamonds_service після оновлення)
    # ================================================================

    async def sync_streamers(self) -> None:
        await asyncio.get_event_loop().run_in_executor(None, self._sync_streamers_sync)

    async def sync_errors(self) -> None:
        await asyncio.get_event_loop().run_in_executor(None, self._sync_errors_sync)

    async def sync_mentors(self) -> None:
        await asyncio.get_event_loop().run_in_executor(None, self._sync_mentors_sync)

    async def sync_gifters(self) -> None:
        await asyncio.get_event_loop().run_in_executor(None, self._sync_gifters_sync)

    # ================================================================
    # СИНХРОННІ МЕТОДИ (виконуються в executor)
    # ================================================================

    def _sync_streamers_sync(self) -> None:
        ws = self._get_or_create_worksheet(SHEET_STREAMERS, HEADERS_STREAMERS)
        streamers = self.db.get_all_streamers_full()

        rows = [HEADERS_STREAMERS]
        for s in streamers:
            diamonds_now = s.get('diamonds_now') or 0
            diamonds_current = s.get('diamonds_current_month') or 0
            diamonds_previous = s.get('diamonds_previous_month') or 0
            diamonds_diff = s.get('diamonds_diff') or 0

            # Якщо стрімер "видалений" з Tango (diamonds_current == -1)
            if diamonds_current == -1:
                diamonds_current_str = "видалено"
            else:
                diamonds_current_str = str(diamonds_current)

            created_at = s.get('created_at', '')
            try:
                dt = datetime.fromisoformat(created_at)
                created_str = dt.strftime('%d.%m.%Y')
            except Exception:
                created_str = created_at

            rows.append([
                s.get('user_id', ''),
                s.get('name', ''),
                s.get('profile_url', ''),
                f"@{s['tg_name']}" if s.get('tg_name') else '',
                s.get('instagram_url', ''),
                s.get('platform', ''),
                s.get('mentor_name', ''),
                str(diamonds_now),
                diamonds_current_str,
                str(diamonds_previous),
                str(diamonds_diff),
                created_str,
            ])

        ws.clear()
        ws.update(rows, value_input_option='RAW')
        logging.info(f"Sheets: синхронізовано {len(streamers)} стрімерів")

    def _sync_mentors_sync(self) -> None:
        ws = self._get_or_create_worksheet(SHEET_MENTORS, HEADERS_MENTORS)
        mentors = self.db.get_all_mentors()
        stats = self.db.get_mentor_statistics()

        rows = [HEADERS_MENTORS]
        for m in mentors:
            mentor_id, name, user_id, profile_url, tg_username, tg_chat_id, \
                instagram, activation_code, last_assigned, created_at = m

            is_activated = "Так" if tg_chat_id else "Ні"
            streamer_count = stats.get(name, {}).get('count', 0)

            try:
                created_str = datetime.fromisoformat(created_at).strftime('%d.%m.%Y')
            except Exception:
                created_str = created_at or ''

            rows.append([
                str(user_id),
                name,
                profile_url,
                f"@{tg_username}" if tg_username else '',
                instagram or '',
                is_activated,
                str(streamer_count),
                created_str,
            ])

        ws.clear()
        ws.update(rows, value_input_option='RAW')
        logging.info(f"Sheets: синхронізовано {len(mentors)} менторів")

    def _sync_gifters_sync(self) -> None:
        ws = self._get_or_create_worksheet(SHEET_GIFTERS, HEADERS_GIFTERS)
        gifters = self.db.get_all_gifters()

        rows = [HEADERS_GIFTERS]
        for g in gifters:
            name, uid, profile_url, owner_id, created_at, *_ = g
            # Отримуємо ім'я власника
            owner_user = self.db.get_bot_user_by_telegram_id(owner_id)
            owner_name = ''
            if owner_user:
                owner_name = (
                    owner_user.get('first_name') or owner_user.get('username') or str(owner_id)
                )
            try:
                created_str = datetime.fromisoformat(created_at).strftime('%d.%m.%Y')
            except Exception:
                created_str = created_at or ''

            rows.append([str(uid), name, profile_url, owner_name, created_str])

        ws.clear()
        ws.update(rows, value_input_option='RAW')
        logging.info(f"Sheets: синхронізовано {len(gifters)} дарувальників")

    def _sync_errors_sync(self) -> None:
        ws = self._get_or_create_worksheet(SHEET_ERRORS, HEADERS_ERRORS)
        errors = self.db.get_diamonds_errors()

        rows = [HEADERS_ERRORS]
        for e in errors:
            rows.append([
                e.get('created_at', ''),
                e.get('streamer_id', ''),
                e.get('streamer_name', ''),
                e.get('error_text', ''),
                str(e.get('retries', 0)),
            ])

        ws.clear()
        ws.update(rows, value_input_option='RAW')
        logging.info(f"Sheets: синхронізовано {len(errors)} помилок")

    # ================================================================
    # СПОВІЩЕННЯ ПРО ПОМИЛКУ СИНХРОНІЗАЦІЇ
    # ================================================================

    async def _notify_admins_error(self, sheet: str, error: str) -> None:
        if not self.bot:
            return
        text = (
            f"⚠️ <b>Помилка синхронізації Google Sheets</b>\n\n"
            f"Аркуш: <code>{sheet}</code>\n"
            f"Помилка: <code>{error[:300]}</code>"
        )
        for admin_id in self.db.get_admin_and_owner_ids():
            try:
                await self.bot.application.bot.send_message(
                    chat_id=admin_id, text=text, parse_mode='HTML'
                )
            except Exception as exc:
                logging.error(f"Не вдалось сповістити адміна {admin_id}: {exc}")
