"""
Handler'и для роботи з дарувальниками
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup


class GifterHandlers:
    """Обробка всіх операцій з дарувальниками"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def start_add_gifter(self, query, user_id):
        """Початок додавання дарувальника"""
        self.bot.user_states[user_id] = 'waiting_gifter_url'
        
        instruction_msg = await query.edit_message_text(
            "➕ Додавання дарувальника\n\n"
            "Надішліть посилання на профіль або стрім дарувальника:\n\n",
            parse_mode='Markdown'
        )
        
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['instruction_message_id'] = instruction_msg.message_id

    async def process_gifter_url(self, update: Update, url: str, user_id: int):
        """Обробка URL дарувальника через API"""
        if 'tango.me' not in url:
            await update.message.reply_text("❌ Некоректне посилання! Надішліть посилання на Tango.")
            return

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            if user_id in self.bot.temp_data and 'instruction_message_id' in self.bot.temp_data[user_id]:
                await self.bot.application.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=self.bot.temp_data[user_id]['instruction_message_id']
                )
        except Exception:
            pass

        processing_msg = await update.effective_chat.send_message(
            "⏳ Обробляю посилання через API Tango.me..."
        )

        try:
            user_id_scraped, user_name = self.bot.api_client.get_user_id_from_url(url)

            if user_id_scraped and user_name:
                profile_url = f"https://tango.me/profile/{user_id_scraped}"

                # owner_id = user_id (той хто додає)
                existing_gifters = self.bot.db.get_all_gifters(owner_id=user_id)
                existing_gifter = None
                for name, existing_id, existing_profile, owner in existing_gifters:
                    if existing_id == user_id_scraped:
                        existing_gifter = {'name': name, 'id': existing_id, 'profile_url': existing_profile}
                        break

                keyboard = [[InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                if existing_gifter:
                    await processing_msg.edit_text(
                        f"ℹ️ Даний дарувальник вже є у вашому списку!\n\n"
                        f"<b>Ім'я:</b> {existing_gifter['name']}\n"
                        f"<b>ID:</b> <code>{user_id_scraped}</code>",
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                else:
                    success = self.bot.db.add_gifter(user_name, user_id_scraped, profile_url, owner_id=user_id)

                    if hasattr(self.bot, 'sheets_service'):
                        self.bot.sheets_service.schedule_sync('gifters')
                    
                    if success:
                        await processing_msg.edit_text(
                            f"✅ Дарувальника додано успішно!\n\n"
                            f"<b>Ім'я:</b> {user_name}\n"
                            f"<b>ID:</b> <code>{user_id_scraped}</code>",
                            parse_mode='HTML',
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                    else:
                        await processing_msg.edit_text(
                            "❌ Помилка збереження дарувальника!",
                            reply_markup=reply_markup
                        )
            else:
                await processing_msg.edit_text("❌ Не вдалося отримати дані користувача!")

        except Exception as ex:
            logging.error(f"Помилка обробки URL дарувальника: {ex}")
            keyboard = [[InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await processing_msg.edit_text(f"❌ Помилка: {ex}", reply_markup=reply_markup)

        self.bot.user_states.pop(user_id, None)

    async def add_to_base_as_gifter(self, query, user_id):
        """Додати як дарувальника — одразу зберігає без додаткових даних"""
        result = self.bot.temp_data.get(user_id, {}).pop('get_id_result', None)
        if not result:
            await query.edit_message_text("❌ Дані не знайдені. Почніть заново.")
            return

        keyboard = [[InlineKeyboardButton("◀️ Меню дарувальників", callback_data='gifters_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Перевірка дубліката
        existing = self.bot.db.get_all_gifters(owner_id=user_id)
        for name, uid, profile_url, owner in existing:
            if uid == result['tango_id']:
                await query.edit_message_text(
                    f"ℹ️ Дарувальник вже у вашому списку!\n\n"
                    f"<b>Ім'я:</b> {name}\n"
                    f"<b>ID:</b> <code>{uid}</code>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return

        success = self.bot.db.add_gifter(
            result['name'], result['tango_id'], result['profile_url'], owner_id=user_id
        )

        if hasattr(self.bot, 'sheets_service'):
            self.bot.sheets_service.schedule_sync('gifters')
    
        if success:
            await query.edit_message_text(
                f"✅ Дарувальника додано!\n\n"
                f"<b>Ім'я:</b> {result['name']}\n"
                f"<b>ID:</b> <code>{result['tango_id']}</code>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text("❌ Помилка збереження!", reply_markup=reply_markup)

    async def show_all_gifters(self, query):
        """Показати всіх дарувальників"""
        user_id = query.from_user.id
        gifters = self.bot.db.get_all_gifters(owner_id=user_id)

        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if not gifters:
            await query.edit_message_text("❌ База дарувальників порожня!", reply_markup=reply_markup)
            return

        text = f"📋 Всі дарувальники ({len(gifters)}):\n\n"
        for i, (name, uid, profile_url, owner) in enumerate(gifters, 1):
            text += f"{i}. <b>{name}</b>\n   ID: <code>{uid}</code>\n\n"
            if len(text) > 3500:
                text += "..."
                break

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    async def start_remove_gifter(self, query, user_id):
        """Початок видалення дарувальника"""
        gifters = self.bot.db.get_all_gifters(owner_id=user_id)
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if not gifters:
            await query.edit_message_text("❌ База дарувальників порожня!", reply_markup=reply_markup)
            return

        buttons = []
        for name, uid, profile_url, owner in gifters[:15]:
            buttons.append([InlineKeyboardButton(
                f"❌ {name} ({uid[:8]}...)",
                callback_data=f'del_gifter_{uid}'
            )])

        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')])
        await query.edit_message_text(
            "➖ Видалення дарувальника\n\nОберіть дарувальника для видалення:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def delete_gifter(self, query, gifter_id):
        """Видалення дарувальника"""
        user_id = query.from_user.id
        success = self.bot.db.remove_gifter(gifter_id, owner_id=user_id)

        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if success:
            await query.edit_message_text("✅ Дарувальника видалено успішно!", reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Помилка при видаленні дарувальника!", reply_markup=reply_markup)
