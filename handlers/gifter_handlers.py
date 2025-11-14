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
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        processing_msg = await update.effective_chat.send_message(
            "⏳ Обробляю посилання через API Tango.me..."
        )
        
        try:
            # Використовуємо API замість Selenium
            user_id_scraped, user_name = self.bot.api_client.get_user_id_from_url(url)
                
            if user_id_scraped and user_name:
                profile_url = f"https://tango.me/profile/{user_id_scraped}"
                
                existing_gifters = self.bot.db.get_all_gifters()
                existing_gifter = None
                for name, existing_id, existing_profile in existing_gifters:
                    if existing_id == user_id_scraped:
                        existing_gifter = {'name': name, 'id': existing_id, 'profile_url': existing_profile}
                        break
                
                keyboard = [[InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if existing_gifter:
                    await processing_msg.edit_text(
                        f"ℹ️ Даний дарувальник вже є в базі!\n\n"
                        f"**Ім'я:** {existing_gifter['name']}\n"
                        f"**ID:** `{user_id_scraped}`\n"
                        f"**Профіль:** [Переглянути]({existing_gifter['profile_url']})",
                        parse_mode='Markdown',
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
                else:
                    success = self.bot.db.add_gifter(user_name, user_id_scraped, profile_url)
                    
                    if success:
                        await processing_msg.edit_text(
                            f"✅ Дарувальника додано успішно через API!\n\n"
                            f"**Ім'я:** {user_name}\n"
                            f"**ID:** `{user_id_scraped}`\n"
                            f"**Профіль:** [Переглянути]({profile_url})",
                            parse_mode='Markdown',
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
            
            await processing_msg.edit_text(
                f"❌ Помилка: {str(ex)}\n\n"
                f"**Можливі причини:**\n"
                f"• Некоректне посилання\n"
                f"• Проблеми з API Tango.me\n"
                f"• Користувач не знайдений",
                reply_markup=reply_markup
            )
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

    async def show_all_gifters(self, query):
        """Показати всіх дарувальників"""
        gifters = self.bot.db.get_all_gifters()
        if not gifters:
            text = "❌ База дарувальників порожня!"
        else:
            text = f"📋 Всі дарувальники ({len(gifters)}):\n\n"
            for i, (name, user_id, profile_url) in enumerate(gifters, 1):
                text += f"{i}. **{name}**\n   ID: `{user_id}`\n   [Профіль]({profile_url})\n\n"
                
                if len(text) > 3500:
                    text += "... і ще кілька"
                    break
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def start_remove_gifter(self, query, user_id):
        """Початок видалення дарувальника"""
        gifters = self.bot.db.get_all_gifters()
        if not gifters:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ База дарувальників порожня!", reply_markup=reply_markup)
            return
        
        keyboard = []
        for name, user_id_db, profile_url in gifters[:15]:
            keyboard.append([InlineKeyboardButton(f"❌ {name} ({user_id_db[:8]}...)", callback_data=f'del_gifter_{user_id_db}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➖ Видалення дарувальника\n\nОберіть дарувальника для видалення:",
            reply_markup=reply_markup
        )

    async def delete_gifter(self, query, gifter_id):
        """Видалення дарувальника"""
        success = self.bot.db.remove_gifter(gifter_id)
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='gifters_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            await query.edit_message_text(
                "✅ Дарувальника видалено успішно!",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                "❌ Помилка при видаленні дарувальника!",
                reply_markup=reply_markup
            )

