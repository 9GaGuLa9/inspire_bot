"""
Планувальник задач: місячне оновлення діамантів о опівночі UTC
"""
import asyncio
import logging
from datetime import date, datetime, timezone


class TaskScheduler:
    """Простий планувальник на asyncio"""

    def __init__(self, bot):
        self.bot = bot
        self._task = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())
        logging.info("TaskScheduler запущено")

    async def _loop(self) -> None:
        while True:
            now = datetime.now(timezone.utc)
            # Чекаємо до наступної опівночі UTC
            seconds_until_midnight = (
                (24 - now.hour - 1) * 3600
                + (60 - now.minute - 1) * 60
                + (60 - now.second)
            )
            await asyncio.sleep(seconds_until_midnight)

            # Перевіряємо: сьогодні останній день місяця?
            today = date.today()
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]

            if today.day == last_day:
                logging.info("Запускаємо місячне оновлення діамантів (розклад)")
                try:
                    await self.bot.diamonds_service.run_monthly_update()
                except Exception as exc:
                    logging.error(f"Помилка місячного оновлення: {exc}")
