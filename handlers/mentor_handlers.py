"""
Handler'и для роботи з менторами
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup


class MentorHandlers:
    """Обробка всіх операцій з менторами"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def show_mentors_menu(self, query):
        """Головне меню менторів"""
        mentors_count = len(self.bot.db.get_all_mentors())
        stats = self.bot.db.get_mentor_statistics()
        
        keyboard = [
            [InlineKeyboardButton("➕ Додати ментора", callback_data='add_mentor')],
            [InlineKeyboardButton("✏️ Редагувати ментора", callback_data='edit_mentor_select')],
            [InlineKeyboardButton("➖ Видалити ментора", callback_data='remove_mentor')],
            [InlineKeyboardButton("📋 Показати всіх", callback_data='show_mentors')],
            [InlineKeyboardButton("🔄 Відновити видаленого", callback_data='restore_mentor_select')],
            [InlineKeyboardButton("📊 Статистика", callback_data='show_mentor_statistics')],
            [InlineKeyboardButton("◀️ Назад", callback_data='users_base')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎓 Керування менторами\n\n📊 У базі: {mentors_count} менторів\n\nОберіть дію:",
            reply_markup=reply_markup
        )
    
    async def start_add_mentor(self, query, user_id):
        """Початок додавання ментора"""
        self.bot.user_states[user_id] = 'waiting_mentor_url'
        
        instruction_msg = await query.edit_message_text(
            "➕ Додавання ментора\n\n"
            "Надішліть посилання на профіль ментора в Tango.me:\n\n"
            "Приклад: https://tango.me/profile/...",
            parse_mode='Markdown'
        )
        
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['mentor_instruction_message_id'] = instruction_msg.message_id
    
    async def process_mentor_url(self, update: Update, url: str, user_id: int):
        """Обробка URL ментора через API"""
        if 'tango.me' not in url:
            await update.message.reply_text("❌ Некоректне посилання! Надішліть посилання на Tango.")
            return
        
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'mentor_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['mentor_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        processing_msg = await update.effective_chat.send_message(
            "⏳ Обробляю посилання через API Tango.me..."
        )
        
        try:
            user_id_scraped, user_name = self.bot.api_client.get_user_id_from_url(url)
            
            if user_id_scraped and user_name:
                profile_url = f"https://tango.me/profile/{user_id_scraped}"
                existing_mentor = self.bot.db.get_mentor_by_user_id(user_id_scraped)
                
                if existing_mentor:
                    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await processing_msg.edit_text(
                        f"ℹ️ Даний ментор вже є в базі!\n\n"
                        f"**Ім'я:** {existing_mentor['mentor_name']}\n"
                        f"**ID:** `{user_id_scraped}`\n"
                        f"**Профіль:** [Переглянути]({existing_mentor['profile_url']})",
                        parse_mode='Markdown',
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )
                else:
                    self.bot.temp_data[user_id] = {
                        'mentor_user_id': user_id_scraped,
                        'mentor_name': user_name,
                        'profile_url': profile_url
                    }
                    
                    keyboard = [
                        [InlineKeyboardButton("➕ Додати інші дані", callback_data='add_mentor_additional_data')],
                        [InlineKeyboardButton("✅ Завершити", callback_data='finish_mentor_adding')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await processing_msg.edit_text(
                        f"✅ Дані отримано успішно!\n\n"
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
            logging.error(f"Помилка обробки URL ментора: {ex}")
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(
                f"❌ Помилка: {str(ex)}",
                reply_markup=reply_markup
            )
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]
    
    async def show_mentor_additional_data_menu(self, query, user_id):
        """Показати меню додаткових даних ментора (через query.edit_message_text)"""
        if user_id not in self.bot.temp_data:
            await query.edit_message_text("❌ Помилка: дані ментора не знайдені!")
            return

        mentor_data = self.bot.temp_data[user_id]
        keyboard = [
            [InlineKeyboardButton("📱 Telegram", callback_data='add_mentor_telegram')],
            [InlineKeyboardButton("📷 Instagram", callback_data='add_mentor_instagram')],
            [InlineKeyboardButton("✅ Завершити", callback_data='finish_mentor_adding')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "➕ Додавання додаткових даних\n\n<b>Поточні дані ментора:</b>\n"
        text += f"• <b>Ім'я:</b> {mentor_data.get('mentor_name', '—')}\n"
        text += f"• <b>ID:</b> <code>{mentor_data.get('mentor_user_id', '—')}</code>\n"
        if mentor_data.get('telegram_username'):
            text += f"• <b>Telegram:</b> @{mentor_data['telegram_username']}\n"
        if mentor_data.get('instagram_url'):
            text += f"• <b>Instagram:</b> {mentor_data['instagram_url']}\n"
        text += "\nЩо бажаєте додати?"

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    async def start_add_mentor_telegram(self, query, user_id):
        """Початок додавання Telegram ментора"""
        self.bot.user_states[user_id] = 'waiting_mentor_telegram'
        self.bot.temp_data[user_id]['mentor_telegram_instruction_message_id'] = query.message.message_id
        
        await query.edit_message_text(
            "📱 Додавання Telegram\n\n"
            "Надішліть Telegram username ментора (з @ або без):",
            parse_mode='Markdown'
        )
    
    async def process_mentor_telegram(self, update: Update, telegram_input: str, user_id: int):
        """Обробка Telegram username ментора"""
        # Очищаємо стан ПЕРШИМ ДІЛОМ
        self.bot.user_states.pop(user_id, None)

        try:
            await update.message.delete()
        except Exception:
            pass

        try:
            if (user_id in self.bot.temp_data
                    and 'mentor_telegram_instruction_message_id' in self.bot.temp_data[user_id]):
                instruction_msg_id = self.bot.temp_data[user_id].pop(
                    'mentor_telegram_instruction_message_id'
                )
                await update.effective_chat.delete_message(instruction_msg_id)
        except Exception:
            pass

        username = telegram_input.strip().lstrip('@')

        # Перевірка: чи username вже є в bot_users
        existing_bot_user = self.bot.db.get_bot_user_by_username(username)
        if existing_bot_user:
            from config import ROLES, ROLE_EMOJI
            role_name = ROLES.get(existing_bot_user['role'], existing_bot_user['role'])
            emoji = ROLE_EMOJI.get(existing_bot_user['role'], '👤')
            keyboard = [[InlineKeyboardButton("✅ Все одно додати", callback_data='confirm_mentor_telegram'),
                        InlineKeyboardButton("❌ Скасувати", callback_data='add_mentor_additional_data')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Зберігаємо username щоб потім підтвердити
            if user_id in self.bot.temp_data:
                self.bot.temp_data[user_id]['pending_telegram_username'] = username

            await update.effective_chat.send_message(
                f"⚠️ @{username} вже зареєстрований у системі як {emoji} {role_name}.\n\n"
                f"Все одно прив'язати цей Telegram до ментора?",
                reply_markup=reply_markup
            )
            return

        if user_id in self.bot.temp_data:
            self.bot.temp_data[user_id]['telegram_username'] = username

        await update.effective_chat.send_message(
            f"✅ Telegram додано: @{username}"
        )
        await self.send_mentor_additional_data_menu(update.effective_chat, user_id)
    
    async def start_add_mentor_instagram(self, query, user_id):
        """Початок додавання Instagram ментора"""
        self.bot.user_states[user_id] = 'waiting_mentor_instagram'
        self.bot.temp_data[user_id]['mentor_instagram_instruction_message_id'] = query.message.message_id
        
        await query.edit_message_text(
            "📷 Додавання Instagram\n\n"
            "Надішліть посилання на Instagram профіль:",
            parse_mode='Markdown'
        )
    
    async def process_mentor_instagram(self, update: Update, url: str, user_id: int):
        """Обробка Instagram URL ментора"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'mentor_instagram_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['mentor_instagram_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
                del self.bot.temp_data[user_id]['mentor_instagram_instruction_message_id']
        except:
            pass
        
        url = url.strip()
        
        if 'instagram.com' not in url:
            temp_msg = await update.effective_chat.send_message("❌ Некоректне посилання на Instagram!")
            import asyncio
            await asyncio.sleep(3)
            try:
                await temp_msg.delete()
            except:
                pass
            await self.send_mentor_additional_data_menu(update.effective_chat, user_id)
            return
        
        if user_id in self.bot.temp_data:
            self.bot.temp_data[user_id]['instagram_url'] = url
        
        temp_msg = await update.effective_chat.send_message(
            "✅ Instagram додано!\n\nПовертаюся до меню..."
        )
        
        import asyncio
        await asyncio.sleep(2)
        try:
            await temp_msg.delete()
        except:
            pass
        
        await self.send_mentor_additional_data_menu(update.effective_chat, user_id)
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]
    
    async def send_mentor_additional_data_menu(self, chat, user_id):
        """Надсилає меню додаткових даних ментора як нове повідомлення"""
        if user_id not in self.bot.temp_data:
            await chat.send_message("❌ Помилка: дані ментора не знайдені!")
            return

        mentor_data = self.bot.temp_data[user_id]
        keyboard = [
            [InlineKeyboardButton("📱 Telegram", callback_data='add_mentor_telegram')],
            [InlineKeyboardButton("📷 Instagram", callback_data='add_mentor_instagram')],
            [InlineKeyboardButton("✅ Завершити", callback_data='finish_mentor_adding')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "➕ Додавання додаткових даних\n\n<b>Поточні дані ментора:</b>\n"
        text += f"• <b>Ім'я:</b> {mentor_data.get('mentor_name', '—')}\n"
        text += f"• <b>ID:</b> <code>{mentor_data.get('mentor_user_id', '—')}</code>\n"
        if mentor_data.get('telegram_username'):
            text += f"• <b>Telegram:</b> @{mentor_data['telegram_username']}\n"
        if mentor_data.get('instagram_url'):
            text += f"• <b>Instagram:</b> {mentor_data['instagram_url']}\n"
        text += "\nЩо бажаєте додати?"

        try:
            await chat.send_message(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"send_mentor_additional_data_menu error: {e}")
            await chat.send_message(
                "❌ Помилка відображення меню. Використайте /start.",
            )

    async def confirm_mentor_telegram_add(self, query, user_id):
        """Підтвердження додавання Telegram що вже є в bot_users"""
        username = self.bot.temp_data.get(user_id, {}).pop('pending_telegram_username', None)
        if not username:
            await query.answer("❌ Помилка: дані не знайдено", show_alert=True)
            return

        self.bot.temp_data[user_id]['telegram_username'] = username
        await query.edit_message_text(f"✅ Telegram @{username} додано.")
        await self.send_mentor_additional_data_menu(query.message.chat, user_id)

    async def finish_mentor_adding(self, query, user_id):
        """Завершення додавання ментора"""
        if user_id not in self.bot.temp_data:
            await query.edit_message_text("❌ Помилка: дані ментора не знайдені!")
            return

        mentor_data = self.bot.temp_data[user_id]
        success = self.bot.db.add_mentor(
            mentor_name=mentor_data.get('mentor_name'),
            user_id=mentor_data.get('mentor_user_id'),
            profile_url=mentor_data.get('profile_url'),
            telegram_username=mentor_data.get('telegram_username'),
            instagram_url=mentor_data.get('instagram_url')
        )

        if hasattr(self.bot, 'sheets_service'):
            self.bot.sheets_service.schedule_sync('mentors')

        keyboard = [[InlineKeyboardButton("◀️ Меню менторів", callback_data='mentors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if success:
            current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
            text = "✅ Ментора додано успішно!\n\n"
            text += f"<b>Ім'я:</b> {mentor_data.get('mentor_name')}\n"
            text += f"<b>ID:</b> <code>{mentor_data.get('mentor_user_id')}</code>\n"
            text += f"<b>Дата додавання:</b> {current_date}\n"
            text += f"<b>Профіль:</b> {mentor_data.get('profile_url')}\n"
            if mentor_data.get('telegram_username'):
                text += f"<b>Telegram:</b> @{mentor_data['telegram_username']}\n"
            if mentor_data.get('instagram_url'):
                text += f"<b>Instagram:</b> {mentor_data['instagram_url']}\n"

            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        else:
            await query.edit_message_text(
                "❌ Помилка збереження ментора!",
                reply_markup=reply_markup
            )

        self.bot.temp_data.pop(user_id, None)
        self.bot.user_states.pop(user_id, None)
    
    async def add_to_base_as_mentor(self, query, user_id):
        """Додати як ментора — перехід до меню додаткових даних"""
        result = self.bot.temp_data.get(user_id, {}).pop('get_id_result', None)
        if not result:
            await query.edit_message_text("❌ Дані не знайдені. Почніть заново.")
            return

        # Перевірка дубліката
        existing = self.bot.db.get_mentor_by_user_id(result['tango_id'])
        if existing:
            keyboard = [[InlineKeyboardButton("◀️ Меню менторів", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"ℹ️ Ментор вже є в базі!\n\n"
                f"<b>Ім'я:</b> {existing['mentor_name']}\n"
                f"<b>ID:</b> <code>{existing['user_id']}</code>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return

        # Переносимо дані у формат mentor flow
        self.bot.temp_data[user_id] = {
            'mentor_user_id': result['tango_id'],
            'mentor_name': result['name'],
            'profile_url': result['profile_url'],
        }

        await self.send_mentor_additional_data_menu(query.message.chat, user_id)

    async def show_all_mentors(self, query):
        """Показати всіх менторів"""
        mentors = self.bot.db.get_all_mentors()

        if not mentors:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ База менторів порожня!", reply_markup=reply_markup)
            return

        stats = self.bot.db.get_mentor_statistics()
        text = f"📋 Всі ментори ({len(mentors)}):\n\n"

        for mentor_data in mentors:
            mentor_id, mentor_name, user_id, profile_url, tg_username, tg_chat_id, \
                instagram, activation_code, last_assigned, created_at = mentor_data

            streamer_count = stats.get(mentor_name, {}).get('count', 0)
            is_activated = tg_chat_id is not None

            text += f"👤 <b>{mentor_name}</b>\n"
            text += f"   ID: <code>{user_id}</code>\n"
            text += f"   📊 Стрімерів: {streamer_count}\n"
            text += f"   ✅ Активація: {'✓' if is_activated else '✗'}\n"
            if tg_username:
                text += f"   📱 @{tg_username}\n"
            text += f"   <a href='{profile_url}'>Профіль</a>\n\n"

        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    async def show_mentor_statistics(self, query):
        """Показати статистику менторів"""
        stats = self.bot.db.get_mentor_statistics()

        if not stats:
            text = "❌ Немає даних для статистики!"
        else:
            text = "📊 <b>Статистика менторів</b>\n\n"
            sorted_stats = sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True)

            for mentor_name, data in sorted_stats:
                count = data['count']
                last_assigned = data.get('last_assigned')
                is_activated = data.get('is_activated', False)

                text += f"👤 <b>{mentor_name}</b>\n"
                text += f"   📊 Стрімерів: {count}\n"
                text += f"   ✅ Активовано: {'Так' if is_activated else 'Ні'}\n"

                if last_assigned:
                    try:
                        date = datetime.fromisoformat(last_assigned)
                        text += f"   🕐 Останнє призначення: {date.strftime('%d.%m.%Y %H:%M')}\n"
                    except Exception:
                        pass

                text += "\n"

        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def start_remove_mentor(self, query, user_id):
        """Початок видалення ментора"""
        mentors = self.bot.db.get_all_mentors()
        
        if not mentors:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ База менторів порожня!", reply_markup=reply_markup)
            return
        
        stats = self.bot.db.get_mentor_statistics()
        keyboard = []
        
        for mentor_data in mentors:
            mentor_id, mentor_name = mentor_data[0], mentor_data[1]
            streamer_count = stats.get(mentor_name, {}).get('count', 0)
            keyboard.append([InlineKeyboardButton(
                f"❌ {mentor_name} ({streamer_count} стрімерів)", 
                callback_data=f'del_mentor_{mentor_id}'
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➖ Видалення ментора\n\n"
            "⚠️ Увага: стрімери залишаться з ім'ям цього ментора\n\n"
            "Оберіть ментора для видалення:",
            reply_markup=reply_markup
        )
    
    async def confirm_delete_mentor(self, query, mentor_id):
        """Підтвердження та видалення ментора"""
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        
        if not mentor:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ Ментора не знайдено!", reply_markup=reply_markup)
            return
        
        stats = self.bot.db.get_mentor_statistics()
        streamer_count = stats.get(mentor['mentor_name'], {}).get('count', 0)
        
        text = f"⚠️ **Підтвердження видалення**\n\n"
        text += f"**Ментор:** {mentor['mentor_name']}\n"
        text += f"**Стрімерів:** {streamer_count}\n\n"
        text += f"Стрімери залишаться з ім'ям ментора '{mentor['mentor_name']}' для можливості фільтрації.\n\n"
        text += f"Ви впевнені?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Так, видалити", callback_data=f'confirm_del_mentor_{mentor_id}')],
            [InlineKeyboardButton("❌ Скасувати", callback_data='remove_mentor')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def delete_mentor(self, query, mentor_id):
        """Видалення ментора"""
        success = self.bot.db.delete_mentor(int(mentor_id))
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            if hasattr(self.bot, 'sheets_service'):
                self.bot.sheets_service.schedule_sync('mentors')
            await query.edit_message_text(
                "✅ Ментора видалено!\n\n"
                "Ментора можна відновити через меню 'Відновити видаленого'.",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                "❌ Помилка при видаленні ментора!",
                reply_markup=reply_markup
            )
    
    async def show_restore_mentor_list(self, query):
        """Показати список видалених менторів"""
        deleted_mentors = self.bot.db.get_deleted_mentors()

        if not deleted_mentors:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("ℹ️ Немає видалених менторів", reply_markup=reply_markup)
            return

        keyboard = []
        for mentor_data in deleted_mentors:
            mentor_id, mentor_name, user_id, profile_url, tg_username, instagram, deleted_at = mentor_data
            try:
                date_str = datetime.fromisoformat(deleted_at).strftime("%d.%m.%Y")
            except Exception:
                date_str = "невідомо"

            keyboard.append([InlineKeyboardButton(
                f"🔄 {mentor_name} (видалено {date_str})",
                callback_data=f'restore_mentor_{mentor_id}'
            )])

        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🔄 <b>Відновлення ментора</b>\n\nОберіть ментора для відновлення:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def restore_mentor(self, query, mentor_id):
        """Відновлення ментора"""
        success = self.bot.db.restore_mentor(int(mentor_id))
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            if hasattr(self.bot, 'sheets_service'):
                self.bot.sheets_service.schedule_sync('mentors')
            await query.edit_message_text(
                "✅ Ментора відновлено успішно!",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                "❌ Помилка при відновленні ментора!",
                reply_markup=reply_markup
            )

    async def show_edit_mentor_list(self, query):
        """Показати список менторів для редагування"""
        mentors = self.bot.db.get_all_mentors()

        if not mentors:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ База менторів порожня!", reply_markup=reply_markup)
            return

        stats = self.bot.db.get_mentor_statistics()

        keyboard = []
        for mentor_data in mentors:
            mentor_id, mentor_name = mentor_data[0], mentor_data[1]
            streamer_count = stats.get(mentor_name, {}).get('count', 0)
            keyboard.append([InlineKeyboardButton(
                f"✏️ {mentor_name} ({streamer_count} стрімерів)",
                callback_data=f'edit_mentor_{mentor_id}'
            )])

        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='mentors_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "✏️ <b>Редагування ментора</b>\n\nОберіть ментора:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def show_edit_mentor_menu(self, query, user_id, mentor_id):
        """Показати меню редагування ментора"""
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        
        if not mentor:
            await query.edit_message_text("❌ Ментора не знайдено!")
            return
        
        # Зберігаємо ID ментора для редагування
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_mentor_id'] = mentor_id
        
        stats = self.bot.db.get_mentor_statistics()
        streamer_count = stats.get(mentor['mentor_name'], {}).get('count', 0)
        
        # Формуємо текст з поточними даними
        text = f"✏️ **Редагування ментора**\n\n"
        text += f"**Ім'я:** {mentor['mentor_name']}\n"
        text += f"**ID:** `{mentor['user_id']}`\n"
        text += f"**Профіль:** [Переглянути]({mentor['profile_url']})\n"
        text += f"**Стрімерів:** {streamer_count}\n\n"
        
        # Статус активації
        if mentor.get('telegram_chat_id'):
            text += f"✅ Статус: Активовано\n\n"
        else:
            text += f"⚠️ Статус: Не активовано\n\n"
        
        text += "**Що бажаєте змінити?**"
        
        # Кнопки редагування
        keyboard = [
            [InlineKeyboardButton("✏️ Змінити профіль (Tango URL)", callback_data=f'edit_mentor_name_{mentor_id}')],
            [InlineKeyboardButton("📱 Telegram", callback_data=f'show_mentor_telegram_{mentor_id}')],
            [InlineKeyboardButton("📷 Instagram", callback_data=f'show_mentor_instagram_{mentor_id}')]
        ]
        
        # Кнопка активації якщо не активовано
        if not mentor.get('telegram_chat_id'):
            keyboard.append([InlineKeyboardButton("🔗 Згенерувати посилання активації", callback_data=f'send_activation_{mentor_id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='edit_mentor_select')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def show_mentor_telegram_menu(self, query, user_id, mentor_id):
        """Показати меню редагування Telegram ментора"""
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_mentor_id'] = mentor_id
        
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        if not mentor:
            await query.edit_message_text("❌ Ментора не знайдено!")
            return
        
        current_telegram = mentor.get('telegram_username', 'не вказано')
        
        keyboard = []
        
        # Кнопка змінити
        keyboard.append([InlineKeyboardButton("✏️ Змінити", callback_data=f'edit_mentor_telegram_{mentor_id}')])
        
        # Кнопка видалити (тільки якщо є telegram)
        if mentor.get('telegram_username'):
            keyboard.append([InlineKeyboardButton("❌ Видалити", callback_data=f'delete_mentor_telegram_{mentor_id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f'edit_mentor_{mentor_id}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📱 Редагування Telegram\n\n"
            f"**Поточний Telegram:** @{current_telegram}\n\n"
            f"Оберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_mentor_instagram_menu(self, query, user_id, mentor_id):
        """Показати меню редагування Instagram ментора"""
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_mentor_id'] = mentor_id
        
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        if not mentor:
            await query.edit_message_text("❌ Ментора не знайдено!")
            return
        
        current_instagram = mentor.get('instagram_url', 'не вказано')
        
        keyboard = []
        
        # Кнопка змінити
        keyboard.append([InlineKeyboardButton("✏️ Змінити", callback_data=f'edit_mentor_instagram_{mentor_id}')])
        
        # Кнопка видалити (тільки якщо є instagram)
        if mentor.get('instagram_url'):
            keyboard.append([InlineKeyboardButton("❌ Видалити", callback_data=f'delete_mentor_instagram_{mentor_id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f'edit_mentor_{mentor_id}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if mentor.get('instagram_url'):
            text = f"📷 Редагування Instagram\n\n**Поточний Instagram:** [посилання]({current_instagram})\n\nОберіть дію:"
        else:
            text = f"📷 Редагування Instagram\n\n**Поточний Instagram:** {current_instagram}\n\nОберіть дію:"
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def delete_mentor_telegram(self, query, mentor_id):
        """Видалити Telegram ментора"""
        success = self.bot.db.update_mentor_field(mentor_id, 'telegram_username', None)

        if success:
            if hasattr(self.bot, 'sheets_service'):
                self.bot.sheets_service.schedule_sync('mentors')
            await query.answer("✅ Telegram видалено", show_alert=True)
            user_id = query.from_user.id
            await self.show_edit_mentor_menu(query, user_id, mentor_id)
        else:
            await query.answer("❌ Помилка видалення", show_alert=True)

    async def delete_mentor_instagram(self, query, mentor_id):
        """Видалити Instagram ментора"""
        success = self.bot.db.update_mentor_field(mentor_id, 'instagram_url', None)

        if success:
            if hasattr(self.bot, 'sheets_service'):
                self.bot.sheets_service.schedule_sync('mentors')
            await query.answer("✅ Instagram видалено", show_alert=True)
            user_id = query.from_user.id
            await self.show_edit_mentor_menu(query, user_id, mentor_id)
        else:
            await query.answer("❌ Помилка видалення", show_alert=True)

    async def start_edit_mentor_name(self, query, user_id, mentor_id):
        """Початок редагування профілю (через новий URL)"""
        self.bot.user_states[user_id] = 'waiting_edit_mentor_url'
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_mentor_id'] = mentor_id
        
        instruction_msg = await query.edit_message_text(
            "✏️ **Редагування профілю ментора**\n\n"
            "Надішліть нове посилання на профіль Tango.me:",
            parse_mode='Markdown'
        )
        self.bot.temp_data[user_id]['edit_mentor_instruction_message_id'] = instruction_msg.message_id
    
    async def process_edit_mentor_url(self, update: Update, url: str, user_id: int):
        """Обробка нового URL ментора"""
        if 'tango.me' not in url:
            await update.message.reply_text("❌ Некоректне посилання! Надішліть посилання на Tango.")
            return
        
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'edit_mentor_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['edit_mentor_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        mentor_id = self.bot.temp_data.get(user_id, {}).get('editing_mentor_id')
        if not mentor_id:
            await update.effective_chat.send_message("❌ Помилка: ID ментора не знайдено!")
            return
        
        processing_msg = await update.effective_chat.send_message("⏳ Обробляю посилання...")
        
        try:
            user_id_scraped, user_name = self.bot.api_client.get_user_id_from_url(url)
            
            if user_id_scraped and user_name:
                profile_url = f"https://tango.me/profile/{user_id_scraped}"
                mentor = self.bot.db.get_mentor_by_id(mentor_id)
                
                if not mentor:
                    await processing_msg.edit_text("❌ Ментора не знайдено!")
                    return
                
                old_mentor_name = mentor['mentor_name']
                
                # Оновлюємо ментора (не створюємо нового!)
                success = self.bot.db.update_mentor_profile(
                    mentor_id=mentor_id,
                    new_name=user_name,
                    new_user_id=user_id_scraped,
                    new_profile_url=profile_url,
                    old_name=old_mentor_name
                )
                
                if success:
                    if hasattr(self.bot, 'sheets_service'):
                        self.bot.sheets_service.schedule_sync('mentors')
                    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'edit_mentor_{mentor_id}')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await processing_msg.edit_text(
                        f"✅ Профіль оновлено!\n\n"
                        f"**Нове ім'я:** {user_name}\n"
                        f"**Новий ID:** `{user_id_scraped}`\n\n"
                        f"Ім'я ментора також оновлено у всіх стрімерів.",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await processing_msg.edit_text("❌ Помилка оновлення!")
            else:
                await processing_msg.edit_text("❌ Не вдалося отримати дані!")
        except Exception as ex:
            logging.error(f"Помилка: {ex}")
            await processing_msg.edit_text(f"❌ Помилка: {str(ex)}")
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]
    
    async def start_edit_mentor_telegram(self, query, user_id, mentor_id):
        """Початок редагування Telegram ментора"""
        self.bot.user_states[user_id] = 'waiting_edit_mentor_telegram'
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_mentor_id'] = mentor_id
        
        instruction_msg = await query.edit_message_text(
            "📱 **Редагування Telegram**\n\n"
            "Надішліть новий Telegram username:",
            parse_mode='Markdown'
        )
        self.bot.temp_data[user_id]['edit_mentor_instruction_message_id'] = instruction_msg.message_id
    
    async def process_edit_mentor_telegram(self, update: Update, telegram_input: str, user_id: int):
        """Обробка нового Telegram ментора"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'edit_mentor_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['edit_mentor_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        mentor_id = self.bot.temp_data.get(user_id, {}).get('editing_mentor_id')
        if not mentor_id:
            await update.effective_chat.send_message("❌ Помилка: ID ментора не знайдено!")
            return
        
        username = telegram_input.strip().replace('@', '')
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        
        if not mentor:
            await update.effective_chat.send_message("❌ Ментора не знайдено!")
            return
        
        success = self.bot.db.add_mentor(
            mentor_name=mentor['mentor_name'],
            user_id=mentor['user_id'],
            profile_url=mentor['profile_url'],
            telegram_username=username,
            instagram_url=mentor.get('instagram_url')
        )

        if hasattr(self.bot, 'sheets_service'):
            self.bot.sheets_service.schedule_sync('mentors')
    
        if success:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'edit_mentor_{mentor_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                f"✅ Telegram оновлено на: @{username}",
                reply_markup=reply_markup
            )
        else:
            await update.effective_chat.send_message("❌ Помилка оновлення!")
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]
    
    async def start_edit_mentor_instagram(self, query, user_id, mentor_id):
        """Початок редагування Instagram ментора"""
        self.bot.user_states[user_id] = 'waiting_edit_mentor_instagram'
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['editing_mentor_id'] = mentor_id
        
        instruction_msg = await query.edit_message_text(
            "📷 **Редагування Instagram**\n\n"
            "Надішліть нове посилання Instagram:",
            parse_mode='Markdown'
        )
        self.bot.temp_data[user_id]['edit_mentor_instruction_message_id'] = instruction_msg.message_id
    
    async def process_edit_mentor_instagram(self, update: Update, url: str, user_id: int):
        """Обробка нового Instagram ментора"""
        try:
            await update.message.delete()
        except:
            pass
        
        try:
            if user_id in self.bot.temp_data and 'edit_mentor_instruction_message_id' in self.bot.temp_data[user_id]:
                instruction_msg_id = self.bot.temp_data[user_id]['edit_mentor_instruction_message_id']
                await update.effective_chat.delete_message(instruction_msg_id)
        except:
            pass
        
        mentor_id = self.bot.temp_data.get(user_id, {}).get('editing_mentor_id')
        if not mentor_id:
            await update.effective_chat.send_message("❌ Помилка: ID ментора не знайдено!")
            return
        
        url = url.strip()
        
        if 'instagram.com' not in url:
            await update.effective_chat.send_message("❌ Некоректне посилання на Instagram!")
            return
        
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        
        if not mentor:
            await update.effective_chat.send_message("❌ Ментора не знайдено!")
            return
        
        success = self.bot.db.add_mentor(
            mentor_name=mentor['mentor_name'],
            user_id=mentor['user_id'],
            profile_url=mentor['profile_url'],
            telegram_username=mentor.get('telegram_username'),
            instagram_url=url
        )

        if hasattr(self.bot, 'sheets_service'):
            self.bot.sheets_service.schedule_sync('mentors')
    
        if success:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'edit_mentor_{mentor_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_chat.send_message(
                f"✅ Instagram оновлено!",
                reply_markup=reply_markup
            )
        else:
            await update.effective_chat.send_message("❌ Помилка оновлення!")
        
        if user_id in self.bot.user_states:
            del self.bot.user_states[user_id]
    
    async def remove_mentor_field(self, query, user_id, mentor_id, field_name):
        """Видалення поля ментора (Telegram або Instagram)"""
        mentor = self.bot.db.get_mentor_by_id(mentor_id)
        if not mentor:
            await query.edit_message_text("❌ Ментора не знайдено!")
            return
        
        # Підготовка даних без видаленого поля
        update_data = {
            'mentor_name': mentor['mentor_name'],
            'user_id': mentor['user_id'],
            'profile_url': mentor['profile_url'],
            'telegram_username': mentor.get('telegram_username'),
            'instagram_url': mentor.get('instagram_url')
        }
        
        field_labels = {
            'telegram': 'Telegram',
            'instagram': 'Instagram'
        }
        
        # Видаляємо відповідне поле
        if field_name == 'telegram':
            update_data['telegram_username'] = None
        elif field_name == 'instagram':
            update_data['instagram_url'] = None
        
        success = self.bot.db.add_mentor(**update_data)

        if hasattr(self.bot, 'sheets_service'):
            self.bot.sheets_service.schedule_sync('mentors')
    
        if success:
            await query.edit_message_text(
                f"✅ {field_labels.get(field_name, 'Поле')} видалено!\n\n"
                "Повертаюся до меню редагування...",
                parse_mode='Markdown'
            )
            import asyncio
            await asyncio.sleep(1)
            await self.show_edit_mentor_menu(query, user_id, mentor_id)
        else:
            await query.edit_message_text("❌ Помилка видалення поля!")
    
    async def send_activation_link(self, query, mentor_id):
        """Надсилання посилання для активації ментора"""
        logging.info(f"send_activation_link called for mentor_id: {mentor_id}")
        
        try:
            mentor = self.bot.db.get_mentor_by_id(mentor_id)
            
            if not mentor:
                logging.error(f"Mentor not found: {mentor_id}")
                await query.answer("❌ Ментора не знайдено!", show_alert=True)
                return
            
            logging.info(f"Found mentor: {mentor['mentor_name']}")
            
            # Генеруємо код активації
            activation_code = self.bot.db.generate_activation_code(mentor_id)
            
            if not activation_code:
                logging.error(f"Failed to generate activation code for mentor_id: {mentor_id}")
                await query.answer("❌ Помилка генерації коду!", show_alert=True)
                return
            
            logging.info(f"Generated activation code: {activation_code}")
            
            # Отримуємо username бота через message
            from telegram import Bot
            bot_token = self.bot.token
            temp_bot = Bot(token=bot_token)
            bot_info = await temp_bot.get_me()
            bot_username = bot_info.username
            
            activation_link = f"https://t.me/{bot_username}?start=mentor_{activation_code}"
            
            logging.info(f"Activation link: {activation_link}")
            
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'edit_mentor_{mentor_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **Посилання для активації згенеровано!**\n\n"
                f"**Ментор:** {mentor['mentor_name']}\n\n"
                f"Надішліть ментору це посилання:\n"
                f"`{activation_link}`\n\n"
                f"💡 Після переходу за посиланням ментор буде активований і зможе отримувати повідомлення про призначених стрімерів.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logging.info(f"Activation link sent successfully for mentor: {mentor['mentor_name']}")
            
        except Exception as e:
            logging.error(f"Error in send_activation_link: {e}", exc_info=True)
            await query.answer(f"❌ Помилка: {str(e)}", show_alert=True)
    
    async def handle_mentor_activation(self, update: Update, activation_code: str):
        """Обробка активації ментора через посилання"""
        mentor = self.bot.db.get_mentor_by_activation_code(activation_code)
        
        if not mentor:
            await update.message.reply_text(
                "❌ Невірний або застарілий код активації!\n\n"
                "Зверніться до адміністратора для отримання нового посилання."
            )
            return
        
        chat_id = update.effective_user.id
        success = self.bot.db.activate_mentor(activation_code, chat_id)
        
        if success:
            await update.message.reply_text(
                f"✅ Вітаємо, {mentor['mentor_name']}!\n\n"
                f"Ви успішно активовані як ментор.\n"
                f"Тепер ви будете отримувати повідомлення про призначених вам стрімерів."
            )
        else:
            await update.message.reply_text(
                "❌ Помилка активації! Спробуйте ще раз або зверніться до адміністратора."
            )
