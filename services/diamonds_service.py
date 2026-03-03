"""
Сервіс для роботи з діамантами стрімерів
"""
import asyncio
import calendar
import logging
from datetime import date
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DIAMONDS_MAX_RETRIES,
    DIAMONDS_REQUEST_DELAY,
    OWNER_ID,
)


class DiamondsService:
    """Отримання та оновлення кількості діамантів стрімерів"""

    def __init__(self, db, bot=None):
        self.db = db
        self.bot = bot

    # ================================================================
    # ОТРИМАННЯ ДІАМАНТІВ З API
    # ================================================================

    async def fetch_diamonds(self, tango_user_id: str) -> Optional[int]:
        """
        Повертає кількість діамантів або None при помилці.
        Використовує TangoAPIClient (той самий токен що й get_profile).
        """
        loop = asyncio.get_event_loop()

        for attempt in range(1, DIAMONDS_MAX_RETRIES + 1):
            try:
                diamonds = await loop.run_in_executor(
                    None,
                    self.bot.api_client.get_diamonds,
                    tango_user_id,
                )
                if diamonds is not None:
                    return diamonds
                logging.warning(
                    f"fetch_diamonds {tango_user_id}: points=None (спроба {attempt})"
                )
            except Exception as exc:
                logging.warning(
                    f"fetch_diamonds {tango_user_id}: {exc} (спроба {attempt})"
                )
            if attempt < DIAMONDS_MAX_RETRIES:
                await asyncio.sleep(DIAMONDS_REQUEST_DELAY)

        return None

    # ================================================================
    # МАСОВЕ ОНОВЛЕННЯ "ЗАРАЗ" (ручний запуск)
    # ================================================================

    async def update_all_diamonds_now(self, progress_callback=None) -> dict:
        """
        Масово оновлює diamonds_now для всіх стрімерів.
        progress_callback(done, total) — викликається після кожного стрімера.
        Повертає: {'updated': int, 'errors': list[dict], 'total': int}
        """
        streamers = self.db.get_all_streamers_for_diamonds()
        total = len(streamers)
        updated = 0
        errors = []

        for idx, streamer in enumerate(streamers, 1):
            tango_id = streamer['user_id']
            name = streamer['name']

            diamonds = await self.fetch_diamonds(tango_id)

            if diamonds is not None:
                self.db.update_streamer_diamonds_now(tango_id, diamonds)
                updated += 1
            else:
                error_text = (
                    f"Не вдалося отримати дані після {DIAMONDS_MAX_RETRIES} спроб"
                )
                errors.append({'streamer_id': tango_id, 'name': name, 'error': error_text})
                self.db.log_diamonds_error(tango_id, name, error_text, DIAMONDS_MAX_RETRIES)
                logging.error(f"diamonds_now error: {name} ({tango_id}): {error_text}")

            if progress_callback:
                await progress_callback(idx, total)

            await asyncio.sleep(DIAMONDS_REQUEST_DELAY)

        if self.bot and hasattr(self.bot, 'sheets_service'):
            try:
                await self.bot.sheets_service.sync_streamers()
            except Exception as exc:
                logging.error(f"Sheets sync after diamonds_now: {exc}")

        return {'updated': updated, 'errors': errors, 'total': total}

    # ================================================================
    # МІСЯЧНЕ ОНОВЛЕННЯ (автоматичне)
    # ================================================================

    async def run_monthly_update(self) -> dict:
        """
        Виконує місячне оновлення:
        - current_month → previous_month
        - отримує нові diamonds → current_month
        - diamonds_diff = current_month - previous_month
        """
        today_str = date.today().isoformat()

        last_run = self.db.get_setting('last_monthly_diamonds_update')
        if last_run == today_str:
            logging.info("Місячне оновлення вже виконувалось сьогодні — пропускаємо")
            return {'skipped': True}

        logging.info("Починаємо місячне оновлення діамантів...")
        streamers = self.db.get_all_streamers_for_diamonds()
        total = len(streamers)
        updated = 0
        errors = []

        for streamer in streamers:
            tango_id = streamer['user_id']
            name = streamer['name']
            current = streamer.get('diamonds_current_month') or 0

            diamonds = await self.fetch_diamonds(tango_id)

            if diamonds is not None:
                diff = diamonds - current
                self.db.monthly_rotate_diamonds(tango_id, current, diamonds, diff)
                updated += 1
            else:
                error_text = f"Недоступний після {DIAMONDS_MAX_RETRIES} спроб"
                errors.append({'streamer_id': tango_id, 'name': name, 'error': error_text})
                self.db.monthly_rotate_diamonds_deleted(tango_id, current)
                self.db.log_diamonds_error(tango_id, name, error_text, DIAMONDS_MAX_RETRIES)
                logging.error(f"monthly_update error: {name} ({tango_id})")

            await asyncio.sleep(DIAMONDS_REQUEST_DELAY)

        self.db.set_setting('last_monthly_diamonds_update', today_str)

        if self.bot and hasattr(self.bot, 'sheets_service'):
            try:
                await self.bot.sheets_service.sync_streamers()
                await self.bot.sheets_service.sync_errors()
            except Exception as exc:
                logging.error(f"Sheets sync after monthly update: {exc}")

        await self._notify_owner_monthly(total, updated, errors)

        return {'total': total, 'updated': updated, 'errors': errors}

    async def _notify_owner_monthly(self, total: int, updated: int, errors: list) -> None:
        """Надсилає звіт власнику після місячного оновлення"""
        if not self.bot:
            return

        streamers = self.db.get_all_streamers_for_diamonds()
        total_now = sum(s.get('diamonds_now') or 0 for s in streamers)
        total_diff = sum(s.get('diamonds_diff') or 0 for s in streamers)

        text = (
            f"📅 <b>Місячне оновлення діамантів завершено</b>\n\n"
            f"✅ Оновлено: {updated} з {total}\n"
            f"❌ Помилок: {len(errors)}\n\n"
            f"💎 Всього діамантів зараз: {total_now:,}\n"
            f"📈 Заробіток за місяць: {total_diff:,}"
        )

        if errors:
            error_names = ', '.join(e['name'] for e in errors[:5])
            if len(errors) > 5:
                error_names += f" та ще {len(errors) - 5}"
            text += f"\n\n⚠️ Проблемні стрімери: {error_names}"

        try:
            await self.bot.application.bot.send_message(
                chat_id=OWNER_ID,
                text=text,
                parse_mode='HTML',
            )
        except Exception as exc:
            logging.error(f"Не вдалось надіслати звіт власнику: {exc}")

    # ================================================================
    # ПЕРЕВІРКА ПРОПУЩЕНОГО ОНОВЛЕННЯ (викликається при post_init)
    # ================================================================

    async def check_missed_monthly_update(self) -> None:
        """
        Якщо бот не працював в останній день попереднього місяця —
        виконує місячне оновлення зараз.
        """
        today = date.today()
        last_run_str = self.db.get_setting('last_monthly_diamonds_update')

        if not last_run_str:
            return

        last_run = date.fromisoformat(last_run_str)

        if today.month == 1:
            prev_year, prev_month = today.year - 1, 12
        else:
            prev_year, prev_month = today.year, today.month - 1

        last_day_prev = calendar.monthrange(prev_year, prev_month)[1]
        expected_run = date(prev_year, prev_month, last_day_prev)

        if last_run < expected_run:
            logging.warning(
                f"Пропущено місячне оновлення за {expected_run} — запускаємо зараз"
            )
            await self.run_monthly_update()
