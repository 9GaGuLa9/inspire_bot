"""
Handler для кнопки "💎 Діамантів зараз" — масове оновлення
Доступ: mentor і вище
"""
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from role_decorators import mentor_or_higher


class DiamondsHandlers:
    """Обробка UI для оновлення діамантів"""

    def __init__(self, bot):
        self.bot = bot

    @mentor_or_higher
    async def start_update_diamonds(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE,
        user_role=None, user_data=None
    ):
        """Запуск масового оновлення diamonds_now"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id

        # Перевірка: вже виконується?
        if self.bot.temp_data.get('diamonds_update_running'):
            await query.answer(
                "⏳ Оновлення вже виконується, зачекайте...", show_alert=True
            )
            return

        self.bot.temp_data['diamonds_update_running'] = True

        await query.edit_message_text(
            "💎 <b>Оновлення діамантів</b>\n\n"
            "⏳ Підготовка...",
            parse_mode='HTML'
        )

        async def progress_callback(done: int, total: int):
            try:
                await query.edit_message_text(
                    f"💎 <b>Оновлення діамантів</b>\n\n"
                    f"⏳ Оновлено {done} з {total}...",
                    parse_mode='HTML'
                )
            except Exception:
                pass

        try:
            result = await self.bot.diamonds_service.update_all_diamonds_now(
                progress_callback=progress_callback
            )
        finally:
            self.bot.temp_data.pop('diamonds_update_running', None)

        # Загальна статистика
        summary = self.bot.db.get_diamonds_summary()
        total_now = summary['total_now']
        total_diff = summary['total_diff']

        updated = result['updated']
        total = result['total']
        errors = result['errors']

        text = (
            f"💎 <b>Оновлення діамантів завершено</b>\n\n"
            f"✅ Оновлено: {updated} з {total}\n"
            f"❌ Помилок: {len(errors)}\n\n"
            f"💎 Всього зараз: <b>{total_now:,}</b>\n"
            f"📈 Заробіток за місяць: <b>{total_diff:,}</b>"
        )

        if errors:
            error_list = '\n'.join(
                f"  • {e['name']}" for e in errors[:5]
            )
            if len(errors) > 5:
                error_list += f"\n  ... та ще {len(errors) - 5}"
            text += f"\n\n⚠️ <b>Помилки:</b>\n{error_list}"

        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as exc:
            logging.error(f"Помилка відображення результату diamonds: {exc}")

        # Ставимо в чергу синхронізацію Sheets
        if hasattr(self.bot, 'sheets_service'):
            self.bot.sheets_service.schedule_sync('streamers')
            if errors:
                self.bot.sheets_service.schedule_sync('errors')
