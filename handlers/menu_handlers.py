"""
Handler'и для роботи з меню
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import START_MESSAGE, HELP_TEXT


class MenuHandlers:
    """Обробка меню бота"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def show_start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Стартове повідомлення"""
        keyboard = [
            [InlineKeyboardButton("🗂 База користувачів", callback_data='users_base')],
            [InlineKeyboardButton("🔍 Шукати дарувальників", callback_data='search_gifters')],
            [InlineKeyboardButton("ℹ️ Допомога", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            START_MESSAGE,
            reply_markup=reply_markup
        )
    
    async def show_main_menu(self, query):
        """Головне меню"""
        keyboard = [
            [InlineKeyboardButton("🗂 База користувачів", callback_data='users_base')],
            [InlineKeyboardButton("🔍 Шукати дарувальників", callback_data='search_gifters')],
            [InlineKeyboardButton("ℹ️ Допомога", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🤖 Головне меню\n\nОберіть дію:",
            reply_markup=reply_markup
        )
    
    async def show_users_base_menu(self, query):
        """Меню бази користувачів"""
        keyboard = [
            [InlineKeyboardButton("🎥 Стрімери", callback_data='streamers_menu')],
            [InlineKeyboardButton("🎁 Дарувальники", callback_data='gifters_menu')],
            [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗂 База користувачів\n\nОберіть категорію:",
            reply_markup=reply_markup
        )
    
    async def show_streamers_menu(self, query):
        """Меню стрімерів"""
        streamers_count = len(self.bot.db.get_all_streamers())
        keyboard = [
            [InlineKeyboardButton("➕ Додати стрімера", callback_data='add_streamer')],
            [InlineKeyboardButton("➖ Видалити стрімера", callback_data='remove_streamer')],
            [InlineKeyboardButton("📋 Показати всіх", callback_data='show_streamers')],
            [InlineKeyboardButton("🔎 Пошук по імені", callback_data='search_streamer')],
            [InlineKeyboardButton("🔍 Фільтрувати за датою", callback_data='filter_streamers')],
            [InlineKeyboardButton("📊 Статистика", callback_data='show_statistics')],
            [InlineKeyboardButton("◀️ Назад", callback_data='users_base')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎥 Керування стрімерами\n\n📊 У базі: {streamers_count} стрімерів\n\nОберіть дію:",
            reply_markup=reply_markup
        )
    
    async def show_gifters_menu(self, query):
        """Меню дарувальників"""
        gifters_count = len(self.bot.db.get_all_gifters())
        keyboard = [
            [InlineKeyboardButton("➕ Додати дарувальника", callback_data='add_gifter')],
            [InlineKeyboardButton("➖ Видалити дарувальника", callback_data='remove_gifter')],
            [InlineKeyboardButton("📋 Показати всіх", callback_data='show_gifters')],
            [InlineKeyboardButton("◀️ Назад", callback_data='users_base')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎁 Керування дарувальниками\n\n📊 У базі: {gifters_count} дарувальників\n\nОберіть дію:",
            reply_markup=reply_markup
        )
    
    async def show_help(self, query):
        """Показати допомогу"""
        keyboard = [[InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            HELP_TEXT,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_gifters_menu(self, query):
        """Меню дарувальників"""
        gifters_count = len(self.bot.db.get_all_gifters())
        keyboard = [
            [InlineKeyboardButton("➕ Додати дарувальника", callback_data='add_gifter')],
            [InlineKeyboardButton("➖ Видалити дарувальника", callback_data='remove_gifter')],
            [InlineKeyboardButton("📋 Показати всіх", callback_data='show_gifters')],
            [InlineKeyboardButton("◀️ Назад", callback_data='users_base')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎁 Керування дарувальниками\n\n📊 У базі: {gifters_count} дарувальників\n\nОберіть дію:",
            reply_markup=reply_markup
        )
    
    async def start_add_streamer(self, query, user_id):
        """Початок додавання стрімера"""
        self.user_states[user_id] = 'waiting_streamer_url'
        
        instruction_msg = await query.edit_message_text(
            "➕ Додавання стрімера\n\n"
            "Надішліть посилання на профіль або стрім стрімера:\n\n",
            parse_mode='Markdown'
        )
        
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['instruction_message_id'] = instruction_msg.message_id
    
    async def start_add_gifter(self, query, user_id):
        """Початок додавання дарувальника"""
        self.user_states[user_id] = 'waiting_gifter_url'
        
        instruction_msg = await query.edit_message_text(
            "➕ Додавання дарувальника\n\n"
            "Надішліть посилання на профіль або стрім дарувальника:\n\n",
            parse_mode='Markdown'
        )
        
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['instruction_message_id'] = instruction_msg.message_id
    
    async def show_additional_data_menu(self, query, user_id):
        """Показати меню додаткових даних"""
        if user_id not in self.temp_data:
            await query.edit_message_text("❌ Помилка: дані стрімера не знайдені!")
            return
        
        streamer_data = self.temp_data[user_id]
        streamer_name = streamer_data.get('name', 'Невідомий стрімер')
        
        keyboard = [
            [InlineKeyboardButton("📱 Telegram", callback_data='add_telegram')],
            [InlineKeyboardButton("📷 Instagram", callback_data='add_instagram')],
            [InlineKeyboardButton("📲 iOS/Android", callback_data='add_platform')],
            [InlineKeyboardButton("✅ Завершити", callback_data='finish_adding')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_data = f"**Поточні дані стрімера:**\n"
        current_data += f"• **Ім'я:** {streamer_name}\n"
        current_data += f"• **ID:** `{streamer_data.get('id')}`\n"
        
        if streamer_data.get('tg_name'):
            current_data += f"• **Telegram:** @{streamer_data.get('tg_name')}\n"
        if streamer_data.get('instagram_url'):
            current_data += f"• **Instagram:** [посилання]({streamer_data.get('instagram_url')})\n"
        if streamer_data.get('platform'):
            current_data += f"• **Платформа:** {streamer_data.get('platform')}\n"
        
        await query.edit_message_text(
            f"➕ Додавання додаткових даних\n\n"
            f"{current_data}\n"
            f"Що бажаєте додати?",
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def start_add_telegram(self, query, user_id):
        """Початок додавання Telegram"""
        self.user_states[user_id] = 'waiting_telegram_url'
        self.temp_data[user_id]['telegram_instruction_message_id'] = query.message.message_id
        
        await query.edit_message_text(
            "📱 Додавання Telegram\n\n"
            "Надішліть посилання на Telegram профіль:\n\n",
            parse_mode='Markdown'
        )
    
    async def start_add_instagram(self, query, user_id):
        """Початок додавання Instagram"""
        self.user_states[user_id] = 'waiting_instagram_url'
        self.temp_data[user_id]['instagram_instruction_message_id'] = query.message.message_id
        
        await query.edit_message_text(
            "📷 Додавання Instagram\n\n"
            "Надішліть посилання на Instagram профіль:\n\n",
            parse_mode='Markdown'
        )
    
    async def show_platform_selection(self, query, user_id):
        """Показати вибір платформи"""
        keyboard = [
            [InlineKeyboardButton("📱 iOS", callback_data='platform_ios')],
            [InlineKeyboardButton("🤖 Android", callback_data='platform_android')],
            [InlineKeyboardButton("◀️ Назад", callback_data='add_more_data')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📲 Вибір платформи\n\nОберіть платформу стрімера:",
            reply_markup=reply_markup
        )
    
    async def set_platform(self, query, user_id, platform):
        """Встановлення платформи"""
        if user_id in self.temp_data:
            self.temp_data[user_id]['platform'] = platform
            await query.edit_message_text(
                f"✅ Платформу встановлено: {platform}\n\n"
                "Повертаюся до меню додаткових даних...",
                reply_markup=None
            )
            import asyncio
            await asyncio.sleep(1)
            await self.show_additional_data_menu(query, user_id)
    
    async def finish_streamer_adding(self, query, user_id):
        """Завершення додавання стрімера"""
        if user_id not in self.temp_data:
            await query.edit_message_text("❌ Помилка: дані стрімера не знайдені!")
            return
        
        streamer_data = self.temp_data[user_id]
        
        success = self.bot.db.add_streamer(
            name=streamer_data.get('name'),
            user_id=streamer_data.get('id'),
            profile_url=streamer_data.get('profile_url'),
            tg_name=streamer_data.get('tg_name'),
            tg_url=streamer_data.get('tg_url'),
            instagram_url=streamer_data.get('instagram_url'),
            platform=streamer_data.get('platform')
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_streamer_{streamer_data.get('id')}")],
            [InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            # Отримуємо дату додавання
            current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
            
            report = f"✅ Стрімера додано успішно!\n\n"
            report += f"**Ім'я:** {streamer_data.get('name')}\n"
            report += f"**ID:** `{streamer_data.get('id')}`\n"
            report += f"**Дата додавання:** {current_date}\n"
            report += f"**Профіль:** `{streamer_data.get('profile_url')}` 📋\n"

            if streamer_data.get('tg_name'):
                tg_url = f"https://t.me/{streamer_data.get('tg_name').replace('@', '')}"
                report += f"**Telegram:** `{tg_url}` 📋\n"

            if streamer_data.get('instagram_url'):
                report += f"**Instagram:** `{streamer_data.get('instagram_url')}` 📋\n"
            
            if streamer_data.get('platform'):
                report += f"**Платформа:** {streamer_data.get('platform')}\n"
            
            empty_fields = []
            if not streamer_data.get('tg_name'):
                empty_fields.append("Telegram")
            if not streamer_data.get('instagram_url'):
                empty_fields.append("Instagram")
            if not streamer_data.get('platform'):
                empty_fields.append("Платформа")
            
            if empty_fields:
                report += f"\n*Незаповнені поля: {', '.join(empty_fields)}*"
            
            await query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        else:
            await query.edit_message_text(
                "❌ Помилка збереження стрімера!",
                reply_markup=reply_markup
            )
        
        if user_id in self.temp_data:
            del self.temp_data[user_id]
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def process_streamer_url(self, update: Update, url: str, user_id: int):
        """Обробка URL стрімера через API"""
        if 'tango.me' not in url:
            await update.message.reply_text("❌ Некоректне посилання! Надішліть посилання на Tango.")
            return
        
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        processing_msg = await update.effective_chat.send_message(
            "⏳ Обробляю посилання через API Tango.me..."
        )
        
        try:
            # Використовуємо API замість Selenium
            user_id_scraped, user_name = self.api_client.get_user_id_from_url(url)
                
            if user_id_scraped and user_name:
                profile_url = f"https://tango.me/profile/{user_id_scraped}"
                existing_streamer = self.bot.db.get_streamer_by_id(user_id_scraped)
                
                if existing_streamer:
                    self.temp_data[user_id] = {
                        'id': user_id_scraped,
                        'name': existing_streamer['name'],
                        'profile_url': existing_streamer['profile_url'],
                        'tg_name': existing_streamer.get('tg_name'),
                        'tg_url': existing_streamer.get('tg_url'),
                        'instagram_url': existing_streamer.get('instagram_url'),
                        'platform': existing_streamer.get('platform')
                    }
                    
                    # Форматуємо дату додавання
                    try:
                        created_at = existing_streamer.get('created_at')
                        if created_at:
                            date = datetime.fromisoformat(created_at)
                            date_str = date.strftime("%d.%m.%Y %H:%M")
                        else:
                            date_str = "невідомо"
                    except:
                        date_str = "невідомо"
                    
                    existing_data = f"**Існуючі дані стрімера:**\n"
                    existing_data += f"• **Ім'я:** {existing_streamer['name']}\n"
                    existing_data += f"• **ID:** `{user_id_scraped}`\n"
                    existing_data += f"• **Додано:** {date_str}\n"
                    existing_data += f"• **Профіль:** [Переглянути]({existing_streamer['profile_url']})\n"
                    
                    if existing_streamer.get('tg_name'):
                        existing_data += f"• **Telegram:** @{existing_streamer.get('tg_name')}\n"
                    if existing_streamer.get('instagram_url'):
                        existing_data += f"• **Instagram:** [посилання]({existing_streamer.get('instagram_url')})\n"
                    if existing_streamer.get('platform'):
                        existing_data += f"• **Платформа:** {existing_streamer.get('platform')}\n"
                    
                    keyboard = [
                        [InlineKeyboardButton("➕ Додати інші дані", callback_data='add_more_data')],
                        [InlineKeyboardButton("✅ Завершити", callback_data='finish_adding')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await processing_msg.edit_text(
                        f"ℹ️ Даний користувач вже є в базі!\n\n"
                        f"{existing_data}\n"
                        f"Бажаєте додати або змінити додаткові дані?",
                        parse_mode='Markdown',
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
                else:
                    self.temp_data[user_id] = {
                        'id': user_id_scraped,
                        'name': user_name,
                        'profile_url': profile_url
                    }
                    
                    keyboard = [
                        [InlineKeyboardButton("➕ Додати інші дані", callback_data='add_more_data')],
                        [InlineKeyboardButton("✅ Завершити", callback_data='finish_adding')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await processing_msg.edit_text(
                        f"✅ Дані отримано успішно через API!\n\n"
                        f"**Ім'я:** {user_name}\n"
                        f"**ID:** `{user_id_scraped}`\n"
                        f"**Профіль:** [Переглянути]({profile_url})\n\n"
                        f"Бажаєте додати додаткові дані?",
                        parse_mode='Markdown',
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
            else:
                await processing_msg.edit_text("❌ Не вдалося отримати дані користувача!")
                    
        except Exception as ex:
            logging.error(f"Помилка обробки URL стрімера: {ex}")
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
            if user_id in self.temp_data and 'instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        processing_msg = await update.effective_chat.send_message(
            "⏳ Обробляю посилання через API Tango.me..."
        )
        
        try:
            # Використовуємо API замість Selenium
            user_id_scraped, user_name = self.api_client.get_user_id_from_url(url)
                
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
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def process_telegram_url(self, update: Update, url: str, user_id: int):
        """Обробка Telegram URL"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'telegram_instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['telegram_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
                del self.temp_data[user_id]['telegram_instruction_message_id']
        except Exception as e:
            logging.error(f"Помилка видалення інструктивного повідомлення Telegram: {e}")
            
        try:
            url = url.strip()
            username = None
            
            if 't.me/' in url:
                username = url.split('t.me/')[-1].split('/')[0].split('?')[0]
            elif url.startswith('@'):
                username = url[1:]
            elif not url.startswith('http') and not url.startswith('@'):
                username = url
            
            if not username:
                temp_msg = await update.effective_chat.send_message("❌ Некоректне посилання на Telegram!")
                import asyncio
                await asyncio.sleep(3)
                try:
                    await temp_msg.delete()
                except:
                    pass
                await self.send_additional_data_menu(update.effective_chat, user_id)
                return
            
            if user_id in self.temp_data:
                self.temp_data[user_id]['tg_name'] = username
                self.temp_data[user_id]['tg_url'] = f"https://t.me/{username}"
            
            temp_success = await update.effective_chat.send_message(
                f"✅ Telegram додано: @{username}\n\n"
                "Повертаюся до меню додаткових даних..."
            )
            
            import asyncio
            await asyncio.sleep(2)
            try:
                await temp_success.delete()
            except:
                pass
            
            await self.send_additional_data_menu(update.effective_chat, user_id)
            
        except Exception as ex:
            logging.error(f"Помилка обробки Telegram URL: {ex}")
            temp_error = await update.effective_chat.send_message(f"❌ Помилка обробки Telegram: {str(ex)}")
            import asyncio
            await asyncio.sleep(5)
            try:
                await temp_error.delete()
            except:
                pass
            await self.send_additional_data_menu(update.effective_chat, user_id)
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def process_instagram_url(self, update: Update, url: str, user_id: int):
        """Обробка Instagram URL"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'instagram_instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['instagram_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
                del self.temp_data[user_id]['instagram_instruction_message_id']
        except Exception as e:
            logging.error(f"Помилка видалення інструктивного повідомлення Instagram: {e}")
            
        try:
            url = url.strip()
            
            if 'instagram.com' not in url:
                temp_msg = await update.effective_chat.send_message("❌ Некоректне посилання на Instagram!")
                import asyncio
                await asyncio.sleep(3)
                try:
                    await temp_msg.delete()
                except:
                    pass
                await self.send_additional_data_menu(update.effective_chat, user_id)
                return
            
            if user_id in self.temp_data:
                self.temp_data[user_id]['instagram_url'] = url
            
            temp_success = await update.effective_chat.send_message(
                f"✅ Instagram додано!\n\n"
                "Повертаюся до меню додаткових даних..."
            )
            
            import asyncio
            await asyncio.sleep(2)
            try:
                await temp_success.delete()
            except:
                pass
            
            await self.send_additional_data_menu(update.effective_chat, user_id)
            
        except Exception as ex:
            logging.error(f"Помилка обробки Instagram URL: {ex}")
            temp_error = await update.effective_chat.send_message(f"❌ Помилка обробки Instagram: {str(ex)}")
            import asyncio
            await asyncio.sleep(5)
            try:
                await temp_error.delete()
            except:
                pass
            await self.send_additional_data_menu(update.effective_chat, user_id)
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def send_additional_data_menu(self, chat, user_id):
        """Надсилає меню додаткових даних як нове повідомлення"""
        if user_id not in self.temp_data:
            await chat.send_message("❌ Помилка: дані стрімера не знайдені!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📱 Telegram", callback_data='add_telegram')],
            [InlineKeyboardButton("📷 Instagram", callback_data='add_instagram')],
            [InlineKeyboardButton("📲 iOS/Android", callback_data='add_platform')],
            [InlineKeyboardButton("✅ Завершити", callback_data='finish_adding')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        streamer_data = self.temp_data[user_id]
        current_data = f"**Поточні дані стрімера:**\n"
        current_data += f"• **Ім'я:** {streamer_data.get('name')}\n"
        current_data += f"• **ID:** `{streamer_data.get('id')}`\n"
        
        if streamer_data.get('tg_name'):
            current_data += f"• **Telegram:** @{streamer_data.get('tg_name')}\n"
        if streamer_data.get('instagram_url'):
            current_data += f"• **Instagram:** [посилання]({streamer_data.get('instagram_url')})\n"
        if streamer_data.get('platform'):
            current_data += f"• **Платформа:** {streamer_data.get('platform')}\n"
        
        await chat.send_message(
            f"➕ Додавання додаткових даних\n\n"
            f"{current_data}\n"
            f"Що бажаєте додати?",
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def start_remove_streamer(self, query, user_id):
        """Початок видалення стрімера"""
        await self.show_delete_page(query, user_id, page=0)
    
    async def show_delete_page(self, query, user_id, page: int = 0):
        """Показати сторінку для видалення стрімерів"""
        streamers = self.bot.db.get_all_streamers()
        total = len(streamers)
        
        if not streamers:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ База стрімерів порожня!", reply_markup=reply_markup)
            return
        
        # Розрахунок пагінації
        total_pages = (total + DELETE_ITEMS_PER_PAGE - 1) // DELETE_ITEMS_PER_PAGE
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * DELETE_ITEMS_PER_PAGE
        end_idx = min(start_idx + DELETE_ITEMS_PER_PAGE, total)
        page_streamers = streamers[start_idx:end_idx]
        
        # Формуємо кнопки
        keyboard = []
        for streamer_data in page_streamers:
            name = streamer_data[0]
            user_id_db = streamer_data[1]
            # Обрізаємо ID для показу
            short_id = user_id_db[:12] + "..." if len(user_id_db) > 12 else user_id_db
            keyboard.append([InlineKeyboardButton(
                f"❌ {name} ({short_id})", 
                callback_data=f'del_streamer_{user_id_db}'
            )])
        
        # Кнопки навігації
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f'page_delete_{page-1}'))
        
        nav_buttons.append(InlineKeyboardButton(
            f"📄 {page + 1}/{total_pages}", 
            callback_data='noop'  # Не робить нічого
        ))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f'page_delete_{page+1}'))
        
        keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"➖ Видалення стрімера\n\n"
            f"📊 Всього: {total} стрімерів\n"
            f"📄 Сторінка {page + 1} з {total_pages}\n\n"
            f"Оберіть стрімера для видалення:",
            reply_markup=reply_markup
        )
    
    async def start_search_streamer(self, query, user_id):
        """Початок пошуку стрімера по імені"""
        self.user_states[user_id] = 'waiting_search_query'
        
        instruction_msg = await query.edit_message_text(
            "🔎 Пошук стрімера\n\n"
            "Введіть ім'я стрімера (або частину імені) для пошуку:\n\n"
            "Приклад: `Олена` або `олена123`\n\n"
            "💡 Пошук не чутливий до регістру",
            parse_mode='Markdown'
        )
        
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['search_instruction_message_id'] = instruction_msg.message_id

    
    async def process_search_query(self, update: Update, query_text: str, user_id: int):
        """Обробка пошукового запиту"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'search_instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['search_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        # Пошук в базі (регістронезалежний)
        all_streamers = self.bot.db.get_all_streamers()
        query_lower = query_text.lower()
        
        found_streamers = [
            s for s in all_streamers 
            if query_lower in s[0].lower()  # s[0] - це name
        ]
        
        if not found_streamers:
            keyboard = [[InlineKeyboardButton("🔎 Новий пошук", callback_data='search_streamer')],
                        [InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                f"😔 Нічого не знайдено за запитом: `{query_text}`\n\n"
                f"Спробуйте інший запит.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            text = f"🔎 Результати пошуку: `{query_text}`\n\n"
            text += f"📊 Знайдено: {len(found_streamers)} стрімерів\n\n"
            
            # Показуємо перші 10 для компактності
            display_limit = 10
            for i, streamer_data in enumerate(found_streamers[:display_limit], 1):
                name, user_id_db, profile_url, tg_name, tg_url, instagram_url, platform, created_at = streamer_data
                
                try:
                    date = datetime.fromisoformat(created_at)
                    date_str = date.strftime("%d.%m.%Y")
                except:
                    date_str = "невідомо"
                
                text += f"{i}. **{name}** (додано: {date_str})\n"
                text += f"   ID: `{user_id_db}`\n"
                text += f"   [Профіль]({profile_url})\n"
                
                if tg_name:
                    text += f"   📱 @{tg_name}\n"
                if instagram_url:
                    text += f"   📷 [Instagram]({instagram_url})\n"
                if platform:
                    text += f"   📲 {platform}\n"
                
                text += "\n"
            
            if len(found_streamers) > display_limit:
                text += f"... та ще {len(found_streamers) - display_limit} стрімерів\n\n"
                text += f"💡 Показано перших {display_limit} результатів\n"
            
            # Кнопки редагування для кожного знайденого стрімера (перших 10)
            keyboard = []
            for streamer_data in found_streamers[:display_limit]:
                name = streamer_data[0]
                user_id_db = streamer_data[1]
                # Обрізаємо ім'я якщо довге
                short_name = name[:20] + "..." if len(name) > 20 else name
                keyboard.append([InlineKeyboardButton(
                    f"✏️ {short_name}", 
                    callback_data=f'edit_streamer_{user_id_db}'
                )])
            
            keyboard.append([InlineKeyboardButton("🔎 Новий пошук", callback_data='search_streamer')])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.temp_data and 'search_instruction_message_id' in self.temp_data[user_id]:
            del self.temp_data[user_id]['search_instruction_message_id']
    
    async def show_edit_streamer_menu(self, query, user_id, streamer_id):
        """Показати меню редагування стрімера"""
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        
        if not streamer:
            await query.edit_message_text("❌ Стрімера не знайдено!")
            return
        
        # Зберігаємо ID стрімера для редагування
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        # Формуємо текст з поточними даними
        text = f"✏️ **Редагування стрімера**\n\n"
        text += f"**Ім'я:** {streamer['name']}\n"
        text += f"**ID:** `{streamer['user_id']}`\n"
        text += f"**Профіль:** [Переглянути]({streamer['profile_url']})\n\n"
        
        text += "**Додаткові дані:**\n"
        if streamer.get('tg_name'):
            text += f"📱 Telegram: @{streamer['tg_name']}\n"
        else:
            text += f"📱 Telegram: _не вказано_\n"
        
        if streamer.get('instagram_url'):
            text += f"📷 Instagram: [посилання]({streamer['instagram_url']})\n"
        else:
            text += f"📷 Instagram: _не вказано_\n"
        
        if streamer.get('platform'):
            text += f"📲 Платформа: {streamer['platform']}\n"
        else:
            text += f"📲 Платформа: _не вказано_\n"
        
        # Кнопки редагування
        keyboard = [
            [InlineKeyboardButton("✏️ Змінити ім'я", callback_data=f'edit_name_{streamer_id}')],
            [InlineKeyboardButton("📱 Змінити Telegram", callback_data=f'edit_telegram_{streamer_id}')],
            [InlineKeyboardButton("📷 Змінити Instagram", callback_data=f'edit_instagram_{streamer_id}')],
            [InlineKeyboardButton("📲 Змінити платформу", callback_data=f'edit_platform_{streamer_id}')]
        ]
        
        # Кнопки видалення полів
        delete_buttons = []
        if streamer.get('tg_name'):
            delete_buttons.append(InlineKeyboardButton("🗑 Видалити Telegram", callback_data=f'remove_telegram_{streamer_id}'))
        if streamer.get('instagram_url'):
            delete_buttons.append(InlineKeyboardButton("🗑 Видалити Instagram", callback_data=f'remove_instagram_{streamer_id}'))
        if streamer.get('platform'):
            delete_buttons.append(InlineKeyboardButton("🗑 Видалити платформу", callback_data=f'remove_platform_{streamer_id}'))
        
        if delete_buttons:
            for btn in delete_buttons:
                keyboard.append([btn])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def start_edit_name(self, query, user_id, streamer_id):
        """Початок редагування імені"""
        self.user_states[user_id] = 'waiting_edit_name'
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        instruction_msg = await query.edit_message_text(
            "✏️ **Редагування імені**\n\n"
            "Надішліть нове ім'я стрімера:",
            parse_mode='Markdown'
        )
        self.temp_data[user_id]['edit_instruction_message_id'] = instruction_msg.message_id
    
    async def start_edit_telegram(self, query, user_id, streamer_id):
        """Початок редагування Telegram"""
        self.user_states[user_id] = 'waiting_edit_telegram'
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        instruction_msg = await query.edit_message_text(
            "📱 **Редагування Telegram**\n\n"
            "Надішліть новий Telegram:",
            parse_mode='Markdown'
        )
        self.temp_data[user_id]['edit_instruction_message_id'] = instruction_msg.message_id
    
    async def start_edit_instagram(self, query, user_id, streamer_id):
        """Початок редагування Instagram"""
        self.user_states[user_id] = 'waiting_edit_instagram'
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        instruction_msg = await query.edit_message_text(
            "📷 **Редагування Instagram**\n\n"
            "Надішліть новий Instagram:",
            parse_mode='Markdown'
        )
        self.temp_data[user_id]['edit_instruction_message_id'] = instruction_msg.message_id
    
    async def show_edit_platform_menu(self, query, user_id, streamer_id):
        """Показати меню вибору платформи для редагування"""
        if user_id not in self.temp_data:
            self.temp_data[user_id] = {}
        self.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        keyboard = [
            [InlineKeyboardButton("📱 iOS", callback_data=f'set_platform_{streamer_id}_iOS')],
            [InlineKeyboardButton("🤖 Android", callback_data=f'set_platform_{streamer_id}_Android')],
            [InlineKeyboardButton("◀️ Назад", callback_data=f'edit_streamer_{streamer_id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📲 **Вибір платформи**\n\nОберіть платформу стрімера:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def update_platform(self, query, user_id, streamer_id, platform):
        """Оновлення платформи"""
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        if not streamer:
            await query.edit_message_text("❌ Стрімера не знайдено!")
            return
        
        success = self.bot.db.add_streamer(
            name=streamer['name'],
            user_id=streamer_id,
            profile_url=streamer['profile_url'],
            tg_name=streamer.get('tg_name'),
            tg_url=streamer.get('tg_url'),
            instagram_url=streamer.get('instagram_url'),
            platform=platform
        )
        
        if success:
            await query.edit_message_text(
                f"✅ Платформу оновлено на: **{platform}**\n\n"
                "Повертаюся до меню редагування...",
                parse_mode='Markdown'
            )
            import asyncio
            await asyncio.sleep(1)
            await self.show_edit_streamer_menu(query, user_id, streamer_id)
        else:
            await query.edit_message_text("❌ Помилка оновлення платформи!")
    
    async def remove_field(self, query, user_id, streamer_id, field_name):
        """Видалення поля (Telegram, Instagram або платформи)"""
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        if not streamer:
            await query.edit_message_text("❌ Стрімера не знайдено!")
            return
        
        # Підготовка даних без видаленого поля
        update_data = {
            'name': streamer['name'],
            'user_id': streamer_id,
            'profile_url': streamer['profile_url'],
            'tg_name': streamer.get('tg_name'),
            'tg_url': streamer.get('tg_url'),
            'instagram_url': streamer.get('instagram_url'),
            'platform': streamer.get('platform')
        }
        
        field_labels = {
            'telegram': 'Telegram',
            'instagram': 'Instagram',
            'platform': 'Платформу'
        }
        
        # Видаляємо відповідне поле
        if field_name == 'telegram':
            update_data['tg_name'] = None
            update_data['tg_url'] = None
        elif field_name == 'instagram':
            update_data['instagram_url'] = None
        elif field_name == 'platform':
            update_data['platform'] = None
        
        success = self.bot.db.add_streamer(**update_data)
        
        if success:
            await query.edit_message_text(
                f"✅ {field_labels.get(field_name, 'Поле')} видалено!\n\n"
                "Повертаюся до меню редагування...",
                parse_mode='Markdown'
            )
            import asyncio
            await asyncio.sleep(1)
            await self.show_edit_streamer_menu(query, user_id, streamer_id)
        else:
            await query.edit_message_text("❌ Помилка видалення поля!")
    
    async def process_edit_name(self, update: Update, new_name: str, user_id: int):
        """Обробка нового імені"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'edit_instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['edit_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        streamer_id = self.temp_data.get(user_id, {}).get('editing_streamer_id')
        if not streamer_id:
            await update.effective_chat.send_message("❌ Помилка: ID стрімера не знайдено!")
            return
        
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        if not streamer:
            await update.effective_chat.send_message("❌ Стрімера не знайдено!")
            return
        
        success = self.bot.db.add_streamer(
            name=new_name,
            user_id=streamer_id,
            profile_url=streamer['profile_url'],
            tg_name=streamer.get('tg_name'),
            tg_url=streamer.get('tg_url'),
            instagram_url=streamer.get('instagram_url'),
            platform=streamer.get('platform')
        )
        
        if success:
            keyboard = [[InlineKeyboardButton("◀️ Назад до редагування", callback_data=f'edit_streamer_{streamer_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                f"✅ Ім'я оновлено на: **{new_name}**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.effective_chat.send_message("❌ Помилка оновлення імені!")
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def process_edit_telegram(self, update: Update, telegram_url: str, user_id: int):
        """Обробка нового Telegram"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'edit_instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['edit_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        streamer_id = self.temp_data.get(user_id, {}).get('editing_streamer_id')
        if not streamer_id:
            await update.effective_chat.send_message("❌ Помилка: ID стрімера не знайдено!")
            return
        
        # Парсимо username
        url = telegram_url.strip()
        username = None
        
        if 't.me/' in url:
            username = url.split('t.me/')[-1].split('/')[0].split('?')[0]
        elif url.startswith('@'):
            username = url[1:]
        elif not url.startswith('http') and not url.startswith('@'):
            username = url
        
        if not username:
            await update.effective_chat.send_message("❌ Некоректне посилання на Telegram!")
            return
        
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        if not streamer:
            await update.effective_chat.send_message("❌ Стрімера не знайдено!")
            return
        
        success = self.bot.db.add_streamer(
            name=streamer['name'],
            user_id=streamer_id,
            profile_url=streamer['profile_url'],
            tg_name=username,
            tg_url=f"https://t.me/{username}",
            instagram_url=streamer.get('instagram_url'),
            platform=streamer.get('platform')
        )
        
        if success:
            keyboard = [[InlineKeyboardButton("◀️ Назад до редагування", callback_data=f'edit_streamer_{streamer_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                f"✅ Telegram оновлено на: @{username}",
                reply_markup=reply_markup
            )
        else:
            await update.effective_chat.send_message("❌ Помилка оновлення Telegram!")
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
    async def process_edit_instagram(self, update: Update, instagram_url: str, user_id: int):
        """Обробка нового Instagram"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.temp_data and 'edit_instruction_message_id' in self.temp_data[user_id]:
                instruction_msg_id = self.temp_data[user_id]['edit_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        streamer_id = self.temp_data.get(user_id, {}).get('editing_streamer_id')
        if not streamer_id:
            await update.effective_chat.send_message("❌ Помилка: ID стрімера не знайдено!")
            return
        
        url = instagram_url.strip()
        
        if 'instagram.com' not in url:
            await update.effective_chat.send_message("❌ Некоректне посилання на Instagram!")
            return
        
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        if not streamer:
            await update.effective_chat.send_message("❌ Стрімера не знайдено!")
            return
        
        success = self.bot.db.add_streamer(
            name=streamer['name'],
            user_id=streamer_id,
            profile_url=streamer['profile_url'],
            tg_name=streamer.get('tg_name'),
            tg_url=streamer.get('tg_url'),
            instagram_url=url,
            platform=streamer.get('platform')
        )
        
        if success:
            keyboard = [[InlineKeyboardButton("◀️ Назад до редагування", callback_data=f'edit_streamer_{streamer_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                f"✅ Instagram оновлено!",
                reply_markup=reply_markup
            )
        else:
            await update.effective_chat.send_message("❌ Помилка оновлення Instagram!")
        
        if user_id in self.user_states:
            del self.user_states[user_id]
    
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
    
    async def delete_streamer(self, query, streamer_id):
        """Показ інформації про стрімера перед видаленням з можливістю редагування"""
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        
        if not streamer:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Стрімера не знайдено!",
                reply_markup=reply_markup
            )
            return
        
        # Показуємо інформацію про стрімера з опціями
        text = f"📋 **Інформація про стрімера**\n\n"
        text += f"**Ім'я:** {streamer['name']}\n"
        text += f"**ID:** `{streamer['user_id']}`\n"
        text += f"**Профіль:** [Переглянути]({streamer['profile_url']})\n"
        
        if streamer.get('created_at'):
            try:
                date = datetime.fromisoformat(streamer['created_at'])
                date_str = date.strftime("%d.%m.%Y %H:%M")
                text += f"**Додано:** {date_str}\n"
            except:
                pass
        
        text += "\n**Додаткові дані:**\n"
        if streamer.get('tg_name'):
            text += f"📱 @{streamer['tg_name']}\n"
        if streamer.get('instagram_url'):
            text += f"📷 [Instagram]({streamer['instagram_url']})\n"
        if streamer.get('platform'):
            text += f"📲 {streamer['platform']}\n"
        
        text += f"\n⚠️ Ви впевнені, що хочете видалити цього стрімера?"
        
        keyboard = [
            [InlineKeyboardButton("✏️ Редагувати", callback_data=f'edit_streamer_{streamer_id}')],
            [InlineKeyboardButton("❌ Видалити", callback_data=f'confirm_delete_{streamer_id}')],
            [InlineKeyboardButton("◀️ Назад", callback_data='remove_streamer')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def confirm_delete_streamer(self, query, streamer_id):
        """Підтвердження та видалення стрімера"""
        success = self.bot.db.remove_streamer(streamer_id)
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            await query.edit_message_text(
                "✅ Стрімера видалено успішно!",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                "❌ Помилка при видаленні стрімера!",
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
    
    async def show_all_streamers(self, query):
        """Показати всіх стрімерів з пагінацією (перша сторінка)"""
        await self.show_all_streamers_paginated(query, page=0)
    
    async def show_all_streamers_paginated(self, query, page: int = 0):
        """Показати стрімерів з пагінацією"""
        streamers = self.bot.db.get_all_streamers()
        total = len(streamers)
        
        if not streamers:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ База стрімерів порожня!", reply_markup=reply_markup)
            return
        
        # Розрахунок пагінації
        total_pages = (total + STREAMERS_PER_PAGE - 1) // STREAMERS_PER_PAGE
        page = max(0, min(page, total_pages - 1))  # Обмежуємо page
        
        start_idx = page * STREAMERS_PER_PAGE
        end_idx = min(start_idx + STREAMERS_PER_PAGE, total)
        page_streamers = streamers[start_idx:end_idx]
        
        # Формуємо текст
        text = f"📋 Всі стрімери (сторінка {page + 1}/{total_pages})\n"
        text += f"📊 Всього: {total} стрімерів\n\n"
        
        for i, streamer_data in enumerate(page_streamers, start_idx + 1):
            name, user_id, profile_url, tg_name, tg_url, instagram_url, platform, created_at = streamer_data
            
            # Форматуємо дату
            try:
                date = datetime.fromisoformat(created_at)
                date_str = date.strftime("%d.%m.%Y")
            except:
                date_str = "невідомо"
            
            text += f"{i}. **{name}** (додано: {date_str})\n"
            text += f"   ID: `{user_id}`\n"
            text += f"   [Профіль]({profile_url})\n"
            
            if tg_name:
                text += f"   📱 @{tg_name}\n"
            if instagram_url:
                text += f"   📷 [Instagram]({instagram_url})\n"
            if platform:
                text += f"   📲 {platform}\n"
            
            text += "\n"
        
        # Кнопки редагування для кожного стрімера на сторінці
        keyboard = []
        for streamer_data in page_streamers:
            name = streamer_data[0]
            user_id = streamer_data[1]
            # Обрізаємо ім'я якщо довге
            short_name = name[:20] + "..." if len(name) > 20 else name
            keyboard.append([InlineKeyboardButton(
                f"✏️ {short_name}", 
                callback_data=f'edit_streamer_{user_id}'
            )])
        
        # Кнопки навігації
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Попередня", callback_data=f'page_streamers_{page-1}'))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ Наступна", callback_data=f'page_streamers_{page+1}'))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
