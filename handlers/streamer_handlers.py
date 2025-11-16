"""
Handler'и для роботи зі стрімерами
"""
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from config import MONTHS_UA, STREAMERS_PER_PAGE, DELETE_ITEMS_PER_PAGE


class StreamerHandlers:
    """Обробка всіх операцій зі стрімерами"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def start_add_streamer(self, query, user_id):
        """Початок додавання стрімера"""
        self.bot.user_states[user_id] = 'waiting_streamer_url'
        
        instruction_msg = await query.edit_message_text(
            "➕ Додавання стрімера\n\n"
            "Надішліть посилання на профіль або стрім стрімера:\n\n",
            parse_mode='Markdown'
        )
        
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['instruction_message_id'] = instruction_msg.message_id

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
            if user_id in self.bot.temp_data and 'instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        processing_msg = await update.effective_chat.send_message(
            "⏳ Обробляю посилання через API Tango.me...\n\n"
        )
        
        try:
            # Використовуємо API замість Selenium
            user_id_scraped, user_name = self.bot.api_client.get_user_id_from_url(url)
                
            if user_id_scraped and user_name:
                profile_url = f"https://tango.me/profile/{user_id_scraped}"
                existing_streamer = self.bot.db.get_streamer_by_id(user_id_scraped)
                
                if existing_streamer:
                    self.bot.temp_data[user_id] = {
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
                        [InlineKeyboardButton("✏️ Змінити ім'я", callback_data=f'edit_name_{user_id_scraped}')],
                        [InlineKeyboardButton("📱 Змінити Telegram", callback_data=f'edit_telegram_{user_id_scraped}')],
                        [InlineKeyboardButton("📷 Змінити Instagram", callback_data=f'edit_instagram_{user_id_scraped}')],
                        [InlineKeyboardButton("📲 Змінити платформу", callback_data=f'edit_platform_{user_id_scraped}')],
                        [InlineKeyboardButton("🎓 Змінити ментора", callback_data=f'assign_mentor_{user_id_scraped}')],
                        [InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]
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
                    self.bot.temp_data[user_id] = {
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
            name, user_id, profile_url, tg_name, tg_url, instagram_url, platform, mentor_name, created_at = streamer_data
            
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
            if mentor_name:
                text += f"   🎓 Ментор: {mentor_name}\n"

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

    async def show_filter_menu(self, query, user_id):
        """Меню фільтрації"""
        keyboard = [
            [InlineKeyboardButton("📅 За роком", callback_data='filter_by_year')],
            [InlineKeyboardButton("📆 За місяцем", callback_data='filter_by_month')],
            [InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 Фільтрація стрімерів\n\nОберіть тип фільтрації:",
            reply_markup=reply_markup
        )

    async def show_year_selection(self, query, user_id):
        """Вибір року для фільтрації"""
        years = self.bot.db.get_available_years()
        
        if not years:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='filter_streamers')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Немає даних для фільтрації!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for year in years:
            count = len(self.bot.db.get_streamers_by_year(year))
            keyboard.append([InlineKeyboardButton(f"📅 {year} ({count} стрімерів)", callback_data=f'year_{year}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='filter_streamers')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 Оберіть рік:\n\n",
            reply_markup=reply_markup
        )

    async def show_year_selection_for_month(self, query, user_id):
        """Вибір року для фільтрації по місяцях"""
        years = self.bot.db.get_available_years()
        
        if not years:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='filter_streamers')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Немає даних для фільтрації!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for year in years:
            keyboard.append([InlineKeyboardButton(f"📅 {year}", callback_data=f'year_for_month_{year}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='filter_streamers')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 Спочатку оберіть рік:",
            reply_markup=reply_markup
        )

    async def show_month_selection(self, query, user_id, year: int):
        """Вибір місяця"""
        months = self.bot.db.get_available_months_for_year(year)
        
        logging.info(f"Showing months for year {year}: {months}")
        
        if not months:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='filter_by_month')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Немає стрімерів за {year} рік!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for month in months:
            count = len(self.bot.db.get_streamers_by_month(year, month))
            month_name = MONTHS_UA.get(month, str(month))
            # ВИПРАВЛЕНО: додаємо рік в callback_data
            keyboard.append([InlineKeyboardButton(
                f"📆 {month_name} ({count} стрімерів)", 
                callback_data=f'month_{year}_{month}'
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='filter_by_month')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📆 Оберіть місяць {year} року:",
            reply_markup=reply_markup
        )

    async def show_streamers_by_year(self, query, year: int):
        """Показати стрімерів за роком"""
        streamers = self.bot.db.get_streamers_by_year(year)
        
        if not streamers:
            text = f"❌ Немає стрімерів за {year} рік!"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='filter_by_year')]]
        else:
            text = f"📅 Стрімери за {year} рік ({len(streamers)}):\n\n"
            
            # Показуємо перших 10
            display_limit = 10
            for i, streamer_data in enumerate(streamers[:display_limit], 1):
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
                if mentor_name:
                    text += f"   🎓 Ментор: {mentor_name}\n"

                text += "\n"
            
            if len(streamers) > display_limit:
                text += f"... та ще {len(streamers) - display_limit} стрімерів\n\n"
                text += f"💡 Показано перших {display_limit} результатів\n"
            
            # Кнопки редагування
            keyboard = []
            for streamer_data in streamers[:display_limit]:
                name = streamer_data[0]
                user_id = streamer_data[1]
                short_name = name[:20] + "..." if len(name) > 20 else name
                keyboard.append([InlineKeyboardButton(
                    f"✏️ {short_name}", 
                    callback_data=f'edit_streamer_{user_id}'
                )])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='filter_by_year')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def show_streamers_by_month(self, query, year: int, month: int):
        """Показати стрімерів за місяцем"""
        streamers = self.bot.db.get_streamers_by_month(year, month)
        month_name = MONTHS_UA.get(month, str(month))
        
        logging.info(f"Showing streamers for {year}-{month}: found {len(streamers)} streamers")
        
        if not streamers:
            text = f"❌ Немає стрімерів за {month_name} {year}!"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'back_to_months_{year}')]]
        else:
            text = f"📆 Стрімери за {month_name} {year} ({len(streamers)}):\n\n"
            
            # Показуємо перших 10
            display_limit = 10
            for i, streamer_data in enumerate(streamers[:display_limit], 1):
                name, user_id, profile_url, tg_name, tg_url, instagram_url, platform, created_at = streamer_data
                
                # Форматуємо дату
                try:
                    date = datetime.fromisoformat(created_at)
                    date_str = date.strftime("%d.%m.%Y %H:%M")
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
                if mentor_name:
                    text += f"   🎓 Ментор: {mentor_name}\n"

                text += "\n"
            
            if len(streamers) > display_limit:
                text += f"... та ще {len(streamers) - display_limit} стрімерів\n\n"
                text += f"💡 Показано перших {display_limit} результатів\n"
            
            # Кнопки редагування
            keyboard = []
            for streamer_data in streamers[:display_limit]:
                name = streamer_data[0]
                user_id = streamer_data[1]
                short_name = name[:20] + "..." if len(name) > 20 else name
                keyboard.append([InlineKeyboardButton(
                    f"✏️ {short_name}", 
                    callback_data=f'edit_streamer_{user_id}'
                )])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f'back_to_months_{year}')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def show_statistics(self, query):
        """Показати статистику"""
        stats = self.bot.db.get_streamers_count_by_period()
        total = len(self.bot.db.get_all_streamers())
        
        if not stats:
            text = "❌ Немає даних для статистики!"
        else:
            text = f"📊 **Статистика стрімерів**\n\n"
            text += f"📈 Всього в базі: **{total}** стрімерів\n\n"
            text += "📅 **По періодах:**\n"
            
            # Сортуємо по даті (спочатку нові)
            sorted_stats = sorted(stats.items(), reverse=True)
            
            for period, count in sorted_stats:
                try:
                    year, month = period.split('-')
                    month_name = MONTHS_UA.get(int(month), month)
                    text += f"• {month_name} {year}: **{count}** стрімерів\n"
                except:
                    text += f"• {period}: **{count}** стрімерів\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_additional_data_menu(self, query, user_id):
        """Показати меню додаткових даних"""
        if user_id not in self.bot.temp_data:
            await query.edit_message_text("❌ Помилка: дані стрімера не знайдені!")
            return
        
        streamer_data = self.bot.temp_data[user_id]
        streamer_name = streamer_data.get('name', 'Невідомий стрімер')
        
        keyboard = [
            [InlineKeyboardButton("📱 Telegram", callback_data='add_telegram')],
            [InlineKeyboardButton("📷 Instagram", callback_data='add_instagram')],
            [InlineKeyboardButton("📲 iOS/Android", callback_data='add_platform')],
            [InlineKeyboardButton("🎓 Призначити ментора", callback_data=f'assign_mentor_{streamer_data.get("id")}')],
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
        self.bot.user_states[user_id] = 'waiting_telegram_url'
        self.bot.temp_data[user_id]['telegram_instruction_message_id'] = query.message.message_id
        
        await query.edit_message_text(
            "📱 Додавання Telegram\n\n"
            "Надішліть посилання на Telegram профіль:\n\n",
            parse_mode='Markdown'
        )

    async def process_telegram_url(self, update: Update, url: str, user_id: int):
        """Обробка Telegram URL"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'telegram_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['telegram_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
                del self.bot.temp_data[user_id]['telegram_instruction_message_id']
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
            
            if user_id in self.bot.temp_data:
                self.bot.temp_data[user_id]['tg_name'] = username
                self.bot.temp_data[user_id]['tg_url'] = f"https://t.me/{username}"
            
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
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

    async def start_add_instagram(self, query, user_id):
        """Початок додавання Instagram"""
        self.bot.user_states[user_id] = 'waiting_instagram_url'
        self.bot.temp_data[user_id]['instagram_instruction_message_id'] = query.message.message_id
        
        await query.edit_message_text(
            "📷 Додавання Instagram\n\n"
            "Надішліть посилання на Instagram профіль:\n\n",
            parse_mode='Markdown'
        )

    async def process_instagram_url(self, update: Update, url: str, user_id: int):
        """Обробка Instagram URL"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'instagram_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['instagram_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
                del self.bot.temp_data[user_id]['instagram_instruction_message_id']
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
            
            if user_id in self.bot.temp_data:
                self.bot.temp_data[user_id]['instagram_url'] = url
            
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
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

    async def send_additional_data_menu(self, chat, user_id):
        """Надсилає меню додаткових даних як нове повідомлення"""
        # ВИПРАВЛЕННЯ 2: Отримуємо streamer_data ОДРАЗУ
        streamer_data = self.bot.temp_data[user_id]
        if user_id not in self.bot.temp_data:
            await chat.send_message("❌ Помилка: дані стрімера не знайдені!")
            return  # ВИПРАВЛЕННЯ 1: Додано return!
        
        
        keyboard = [
            [InlineKeyboardButton("📱 Telegram", callback_data='add_telegram')],
            [InlineKeyboardButton("📷 Instagram", callback_data='add_instagram')],
            [InlineKeyboardButton("📲 iOS/Android", callback_data='add_platform')],
            [InlineKeyboardButton("🎓 Призначити ментора", 
            callback_data=f'assign_mentor_{streamer_data.get("id")}')],
            [InlineKeyboardButton("✅ Завершити", callback_data='finish_adding')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        if user_id in self.bot.temp_data:
            self.bot.temp_data[user_id]['platform'] = platform
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
        if user_id not in self.bot.temp_data:
            await query.edit_message_text("❌ Помилка: дані стрімера не знайдені!")
            return
        
        streamer_data = self.bot.temp_data[user_id]
        
        success = self.bot.db.add_streamer(
            name=streamer_data.get('name'),
            user_id=streamer_data.get('id'),
            profile_url=streamer_data.get('profile_url'),
            tg_name=streamer_data.get('tg_name'),
            tg_url=streamer_data.get('tg_url'),
            instagram_url=streamer_data.get('instagram_url'),
            platform=streamer_data.get('platform'),
            mentor_name=streamer_data.get('mentor_name')
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
        
        if user_id in self.bot.temp_data:
            del self.bot.temp_data[user_id]
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

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

    async def show_edit_streamer_menu(self, query, user_id, streamer_id):
        """Показати меню редагування стрімера"""
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        
        if not streamer:
            await query.edit_message_text("❌ Стрімера не знайдено!")
            return
        
        # Зберігаємо ID стрімера для редагування
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        # Формуємо текст з поточними даними
        text = f"✏️ Редагування стрімера\n\n"
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

        if streamer.get('mentor_name'):
            text += f"🎓 Ментор: {streamer['mentor_name']}\n"
        else:
            text += f"🎓 Ментор: _не призначено_\n"
        # Кнопки редагування
        keyboard = [
            [InlineKeyboardButton("✏️ Змінити ім'я", callback_data=f'edit_name_{streamer_id}')],
            [InlineKeyboardButton("📱 Змінити Telegram", callback_data=f'edit_telegram_{streamer_id}')],
            [InlineKeyboardButton("📷 Змінити Instagram", callback_data=f'edit_instagram_{streamer_id}')],
            [InlineKeyboardButton("📲 Змінити платформу", callback_data=f'edit_platform_{streamer_id}')],
            [InlineKeyboardButton("🎓 Змінити ментора", callback_data=f'assign_mentor_{streamer_id}')]  # ДОДАТИ ЦЕ
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
            disable_web_page_preview=True
        )

    async def start_edit_name(self, query, user_id, streamer_id):
        """Початок редагування імені"""
        self.bot.user_states[user_id] = 'waiting_edit_name'
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        instruction_msg = await query.edit_message_text(
            "✏️ **Редагування імені**\n\n"
            "Надішліть нове ім'я стрімера:",
            parse_mode='Markdown'
        )
        self.bot.temp_data[user_id]['edit_instruction_message_id'] = instruction_msg.message_id

    async def process_edit_name(self, update: Update, new_name: str, user_id: int):
        """Обробка нового імені"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'edit_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['edit_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        streamer_id = self.bot.temp_data.get(user_id, {}).get('editing_streamer_id')
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
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

    async def start_edit_telegram(self, query, user_id, streamer_id):
        """Початок редагування Telegram"""
        self.bot.user_states[user_id] = 'waiting_edit_telegram'
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        instruction_msg = await query.edit_message_text(
            "📱 **Редагування Telegram**\n\n"
            "Надішліть новий Telegram:",
            parse_mode='Markdown'
        )
        self.bot.temp_data[user_id]['edit_instruction_message_id'] = instruction_msg.message_id

    async def process_edit_telegram(self, update: Update, telegram_url: str, user_id: int):
        """Обробка нового Telegram"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'edit_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['edit_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        streamer_id = self.bot.temp_data.get(user_id, {}).get('editing_streamer_id')
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
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

    async def start_edit_instagram(self, query, user_id, streamer_id):
        """Початок редагування Instagram"""
        self.bot.user_states[user_id] = 'waiting_edit_instagram'
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
        instruction_msg = await query.edit_message_text(
            "📷 **Редагування Instagram**\n\n"
            "Надішліть новий Instagram:",
            parse_mode='Markdown'
        )
        self.bot.temp_data[user_id]['edit_instruction_message_id'] = instruction_msg.message_id

    async def process_edit_instagram(self, update: Update, instagram_url: str, user_id: int):
        """Обробка нового Instagram"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'edit_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['edit_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        streamer_id = self.bot.temp_data.get(user_id, {}).get('editing_streamer_id')
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
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]

    async def show_edit_platform_menu(self, query, user_id, streamer_id):
        """Показати меню вибору платформи для редагування"""
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_streamer_id'] = streamer_id
        
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

    async def start_search_streamer(self, query, user_id):
        """Початок пошуку стрімера по імені"""
        self.bot.user_states[user_id] = 'waiting_search_query'
        
        instruction_msg = await query.edit_message_text(
            "🔎 Пошук стрімера\n\n"
            "Введіть ім'я стрімера (або частину імені) для пошуку:\n\n"
            "Приклад: `Олена` або `олена123`\n\n"
            "💡 Пошук не чутливий до регістру",
            parse_mode='Markdown'
        )
        
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['search_instruction_message_id'] = instruction_msg.message_id

    async def process_search_query(self, update: Update, query_text: str, user_id: int):
        """Обробка пошукового запиту"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'search_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['search_instruction_message_id']
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
                if mentor_name:
                    text += f"   🎓 Ментор: {mentor_name}\n"

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
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]
        if user_id in self.bot.temp_data and 'search_instruction_message_id' in self.bot.temp_data[user_id]:
            del self.bot.temp_data[user_id]['search_instruction_message_id']

    async def show_mentor_selection(self, query, user_id, streamer_id):
        """Показати список менторів для призначення стрімеру"""
        import logging
        
        # Логування для діагностики
        logging.info(f"show_mentor_selection called with streamer_id: {streamer_id}, type: {type(streamer_id)}")
        
        # Очищуємо streamer_id від зайвих символів
        streamer_id = str(streamer_id).strip()
        logging.info(f"Cleaned streamer_id: {streamer_id}")
        
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        
        if not streamer:
            logging.error(f"Streamer not found for id: {streamer_id}")
            
            # Спробуємо показати що є в базі для діагностики
            all_streamers = self.bot.db.get_all_streamers()
            logging.info(f"Total streamers in DB: {len(all_streamers)}")
            if all_streamers:
                logging.info(f"First streamer user_id: {all_streamers[0][1]}")
            
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='streamers_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ Стрімера не знайдено!\n\n"
                f"**Debug info:**\n"
                f"Шуканий ID: `{streamer_id}`\n"
                f"Стрімерів у БД: {len(all_streamers)}",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        logging.info(f"Streamer found: {streamer['name']}")
        
        # Отримуємо менторів, сортованих за датою останнього призначення
        mentors = self.bot.db.get_all_mentors(sort_by_assignment=True)
        stats = self.bot.db.get_mentor_statistics()
        
        if not mentors:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'edit_streamer_{streamer_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Спочатку додайте менторів через меню 'Ментори'",
                reply_markup=reply_markup
            )
            return
        
        text = f"🎓 **Призначення ментора**\n\n"
        text += f"**Стрімер:** {streamer['name']}\n"
        
        if streamer.get('mentor_name'):
            text += f"**Поточний ментор:** {streamer['mentor_name']}\n"
        else:
            text += f"**Поточний ментор:** _не призначено_\n"
        
        text += f"\n📊 Оберіть ментора:\n"
        text += f"_(відсортовано за датою останнього призначення)_\n"
        
        keyboard = []
        
        # Додаємо кнопку "Без ментора"
        no_mentor_count = stats.get('Без ментора', {}).get('count', 0)
        keyboard.append([InlineKeyboardButton(
            f"⭕ Без ментора ({no_mentor_count} стрімерів)",
            callback_data=f'select_mentor_{streamer_id}_none'
        )])
        
        # Додаємо менторів
        for mentor_data in mentors:
            mentor_id, mentor_name = mentor_data[0], mentor_data[1]
            mentor_stats = stats.get(mentor_name, {})
            count = mentor_stats.get('count', 0)
            is_activated = mentor_stats.get('is_activated', False)
            
            activation_mark = "✅" if is_activated else "⚠️"
            
            keyboard.append([InlineKeyboardButton(
                f"{activation_mark} {mentor_name} ({count} стрімерів)",
                callback_data=f'select_mentor_{streamer_id}_{mentor_name}'
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f'edit_streamer_{streamer_id}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def assign_mentor_to_streamer(self, query, user_id, streamer_id, mentor_identifier):
        """Призначення ментора стрімеру"""
        streamer = self.bot.db.get_streamer_by_id(streamer_id)
        
        if not streamer:
            await query.edit_message_text("❌ Стрімера не знайдено!")
            return
        
        # Визначаємо ім'я ментора
        if mentor_identifier == 'none':
            mentor_name = None
            mentor = None
        else:
            mentor_name = mentor_identifier
            mentor = self.bot.db.get_mentor_by_user_id(mentor_identifier)
            
            # Якщо не знайшли за user_id, шукаємо за ім'ям
            if not mentor:
                mentors = self.bot.db.get_all_mentors()
                for m in mentors:
                    if m[1] == mentor_name:  # m[1] - це mentor_name
                        mentor = self.bot.db.get_mentor_by_id(m[0])
                        break
        
        # Оновлюємо стрімера
        success = self.bot.db.add_streamer(
            name=streamer['name'],
            user_id=streamer_id,
            profile_url=streamer['profile_url'],
            tg_name=streamer.get('tg_name'),
            tg_url=streamer.get('tg_url'),
            instagram_url=streamer.get('instagram_url'),
            platform=streamer.get('platform'),
            mentor_name=mentor_name
        )
        
        if success and mentor_name:
            # Оновлюємо дату останнього призначення ментора
            self.bot.db.update_mentor_last_assigned(mentor_name)
            
            # Відправляємо повідомлення ментору якщо він активований
            if mentor and mentor.get('telegram_chat_id'):
                await self.send_mentor_notification(
                    mentor['telegram_chat_id'],
                    mentor_name,
                    streamer
                )
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'edit_streamer_{streamer_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            if mentor_name:
                msg = f"✅ Ментора призначено!\n\n**Стрімер:** {streamer['name']}\n**Ментор:** {mentor_name}"
                if mentor and not mentor.get('telegram_chat_id'):
                    msg += "\n\n⚠️ Увага: Ментор не активований. Повідомлення не надіслано."
            else:
                msg = f"✅ Ментора прибрано!\n\n**Стрімер:** {streamer['name']}"
            
            await query.edit_message_text(
                msg,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Помилка призначення ментора!",
                reply_markup=reply_markup
            )

    async def send_mentor_notification(self, chat_id, mentor_name, streamer):
        """Відправка повідомлення ментору про призначення стрімера"""
        from datetime import datetime
        
        try:
            text = f"🎯 **Вам призначено нового стрімера!**\n\n"
            text += f"👤 **Ім'я:** {streamer['name']}\n"
            text += f"🆔 **ID:** `{streamer['user_id']}`\n"
            text += f"🔗 **Профіль:** {streamer['profile_url']}\n"
            
            if streamer.get('tg_name'):
                text += f"📱 **Telegram:** @{streamer['tg_name']}\n"
            
            if streamer.get('instagram_url'):
                text += f"📷 **Instagram:** {streamer['instagram_url']}\n"
            
            if streamer.get('platform'):
                text += f"📲 **Платформа:** {streamer['platform']}\n"
            
            current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
            text += f"📅 **Дата призначення:** {current_date}\n"
            
            # Отримуємо bot з context
            from telegram import Bot
            bot_token = self.bot.token
            bot = Bot(token=bot_token)
            
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            return True
        except Exception as e:
            import logging
            logging.error(f"Помилка відправки повідомлення ментору {mentor_name}: {e}")
            return False