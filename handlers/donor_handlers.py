# donor_handlers.py
# Обробники для роботи з особистими даруваниками користувачів

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from role_decorators import *
import re

logger = logging.getLogger(__name__)


class PersonalDonorHandlers:
    """Клас для обробки операцій з особистими даруваниками"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ================================
    # ГОЛОВНЕ МЕНЮ ДАРУВАНИКІВ
    # ================================
    
    @mentor_or_higher
    async def show_my_donors_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 user_role=None, user_data=None):
        """Показує меню особистих даруваників користувача"""
        query = update.callback_query
        if query:
            await query.answer()
        
        user_id = update.effective_user.id
        donors = self.bot.db.get_user_donors(user_id)
        
        text = f"💝 <b>Мої даруваники</b>\n\n📊 Всього: {len(donors)}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📋 Показати всіх", callback_data='my_donors_list')],
            [InlineKeyboardButton("➕ Додати даруваника", callback_data='my_donors_add')],
            [InlineKeyboardButton("🔍 Пошук", callback_data='my_donors_search')],
        ]
        
        # Власник має додатковий доступ до всіх даруваників
        if user_role == 'owner':
            keyboard.insert(1, [InlineKeyboardButton("👥 Всі даруваники користувачів", callback_data='all_users_donors')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='main_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # СПИСОК ДАРУВАНИКІВ
    # ================================
    
    @mentor_or_higher
    async def show_my_donors_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  page: int = 0, user_role=None, user_data=None):
        """Показує список особистих даруваників з пагінацією"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        donors = self.bot.db.get_user_donors(user_id)
        
        if not donors:
            text = "💝 <b>Мої даруваники</b>\n\n📭 Список порожній"
            keyboard = [
                [InlineKeyboardButton("➕ Додати даруваника", callback_data='my_donors_add')],
                [InlineKeyboardButton("◀️ Назад", callback_data='my_donors_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return
        
        # Пагінація: 10 на сторінку
        page_size = 10
        total_pages = (len(donors) + page_size - 1) // page_size
        page = min(max(0, page), total_pages - 1)
        
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(donors))
        page_donors = donors[start_idx:end_idx]
        
        text = f"💝 <b>Мої даруваники</b>\n\n📊 Всього: {len(donors)}\n📄 Сторінка {page + 1}/{total_pages}\n\n"
        
        keyboard = []
        for donor in page_donors:
            donor_name = donor['donor_name']
            donor_id_short = donor['donor_tango_id'][:10] + '...' if len(donor['donor_tango_id']) > 10 else donor['donor_tango_id']
            keyboard.append([
                InlineKeyboardButton(
                    f"{donor_name} ({donor_id_short})",
                    callback_data=f'my_donor_details_{donor["id"]}'
                )
            ])
        
        # Навігація
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f'my_donors_page_{page-1}'))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f'my_donors_page_{page+1}'))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='my_donors_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДЕТАЛІ ДАРУВАНИКА
    # ================================
    
    @mentor_or_higher
    async def show_donor_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                donor_id: int, user_role=None, user_data=None):
        """Показує детальну інформацію про даруваника"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        donors = self.bot.db.get_user_donors(user_id)
        donor = next((d for d in donors if d['id'] == donor_id), None)
        
        if not donor:
            await query.answer("❌ Даруваника не знайдено", show_alert=True)
            return
        
        text = (
            f"💝 <b>{donor['donor_name']}</b>\n\n"
            f"🆔 Tango ID: <code>{donor['donor_tango_id']}</code>\n"
        )
        
        if donor.get('profile_link'):
            text += f"🔗 Профіль: {donor['profile_link']}\n"
        
        if donor.get('notes'):
            text += f"\n📝 Нотатки:\n{donor['notes']}\n"
        
        text += f"\n📅 Доданий: {donor['created_at'][:10]}"
        
        keyboard = [
            [InlineKeyboardButton("✏️ Редагувати", callback_data=f'my_donor_edit_{donor_id}')],
            [InlineKeyboardButton("🗑 Видалити", callback_data=f'my_donor_delete_{donor_id}')],
            [InlineKeyboardButton("◀️ Назад", callback_data='my_donors_list')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДОДАВАННЯ ДАРУВАНИКА
    # ================================
    
    @mentor_or_higher
    async def start_add_donor(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             user_role=None, user_data=None):
        """Початок процесу додавання даруваника"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        self.bot.temp_data[user_id] = {
            'action': 'adding_personal_donor',
            'step': 'enter_profile_link'
        }
        
        keyboard = [[InlineKeyboardButton("❌ Скасувати", callback_data='my_donors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "➕ <b>Додавання даруваника</b>\n\n"
            "Крок 1: Надішліть посилання на профіль Tango даруваника\n\n"
            "Формат: https://www.tango.me/[USERNAME]\n"
            "або просто ім'я користувача"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @mentor_or_higher
    async def process_donor_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_role=None, user_data=None):
        """Обробка посилання на профіль даруваника"""
        user_id = update.effective_user.id
        
        # Перевіряємо чи є активний процес
        if (user_id not in self.bot.temp_data or 
            self.bot.temp_data[user_id].get('action') != 'adding_personal_donor' or
            self.bot.temp_data[user_id].get('step') != 'enter_profile_link'):
            return
        
        text = update.message.text.strip()
        
        # Витягуємо Tango ID з посилання
        tango_id = self._extract_tango_id(text)
        
        if not tango_id:
            await update.message.reply_text(
                "❌ Невірний формат посилання.\n"
                "Надішліть посилання виду: https://www.tango.me/[USERNAME]"
            )
            return
        
        # Отримуємо ім'я з Tango (тут має бути API запит до Tango)
        # Поки що використовуємо tango_id як ім'я
        donor_name = tango_id
        
        # Зберігаємо дані
        self.bot.temp_data[user_id].update({
            'donor_tango_id': tango_id,
            'donor_name': donor_name,
            'profile_link': text if 'tango.me' in text else f'https://www.tango.me/{tango_id}',
            'step': 'enter_notes'
        })
        
        keyboard = [
            [InlineKeyboardButton("⏭ Пропустити", callback_data='my_donor_skip_notes')],
            [InlineKeyboardButton("❌ Скасувати", callback_data='my_donors_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Даруваник: {donor_name}\n"
            f"🆔 ID: <code>{tango_id}</code>\n\n"
            f"Крок 2 (опційно): Надішліть нотатки про даруваника\n"
            f"або натисніть 'Пропустити'",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    @mentor_or_higher
    async def process_donor_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 user_role=None, user_data=None):
        """Обробка нотаток та збереження даруваника"""
        user_id = update.effective_user.id
        
        # Перевіряємо чи є активний процес
        if (user_id not in self.bot.temp_data or 
            self.bot.temp_data[user_id].get('action') != 'adding_personal_donor'):
            return
        
        temp_data = self.bot.temp_data[user_id]
        
        # Якщо це callback (пропустити нотатки)
        if update.callback_query:
            notes = ''
            query = update.callback_query
            await query.answer()
        else:
            notes = update.message.text.strip()
        
        # Зберігаємо даруваника
        donor_id = self.bot.db.add_user_donor(
            user_telegram_id=user_id,
            donor_name=temp_data['donor_name'],
            donor_tango_id=temp_data['donor_tango_id'],
            profile_link=temp_data['profile_link'],
            notes=notes
        )
        
        if donor_id:
            # Логування
            self.bot.db.add_audit_log(
                user_telegram_id=user_id,
                user_name=user_data.get('full_name', ''),
                action_type='add_donor',
                target_type='user_donor',
                target_id=str(donor_id),
                target_name=temp_data['donor_name'],
                details={'tango_id': temp_data['donor_tango_id']}
            )
            
            keyboard = [[InlineKeyboardButton("◀️ До даруваників", callback_data='my_donors_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"✅ <b>Даруваника додано!</b>\n\n"
                f"💝 {temp_data['donor_name']}\n"
                f"🆔 ID: <code>{temp_data['donor_tango_id']}</code>"
            )
            
            if update.callback_query:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            text = "❌ Помилка при додаванні даруваника"
            if update.callback_query:
                await query.answer(text, show_alert=True)
            else:
                await update.message.reply_text(text)
        
        # Очищаємо temp_data
        del self.bot.temp_data[user_id]
    
    # ================================
    # РЕДАГУВАННЯ ДАРУВАНИКА
    # ================================
    
    @mentor_or_higher
    async def show_edit_donor_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  donor_id: int, user_role=None, user_data=None):
        """Показує меню редагування даруваника"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        donors = self.bot.db.get_user_donors(user_id)
        donor = next((d for d in donors if d['id'] == donor_id), None)
        
        if not donor:
            await query.answer("❌ Даруваника не знайдено", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("✏️ Змінити ім'я", callback_data=f'my_donor_edit_name_{donor_id}')],
            [InlineKeyboardButton("🔗 Змінити посилання", callback_data=f'my_donor_edit_link_{donor_id}')],
            [InlineKeyboardButton("📝 Змінити нотатки", callback_data=f'my_donor_edit_notes_{donor_id}')],
            [InlineKeyboardButton("◀️ Назад", callback_data=f'my_donor_details_{donor_id}')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"✏️ <b>Редагування: {donor['donor_name']}</b>\n\nОберіть що змінити:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ВИДАЛЕННЯ ДАРУВАНИКА
    # ================================
    
    @mentor_or_higher
    async def confirm_delete_donor(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  donor_id: int, user_role=None, user_data=None):
        """Підтвердження видалення даруваника"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        donors = self.bot.db.get_user_donors(user_id)
        donor = next((d for d in donors if d['id'] == donor_id), None)
        
        if not donor:
            await query.answer("❌ Даруваника не знайдено", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ Так, видалити", callback_data=f'my_donor_delete_confirm_{donor_id}')],
            [InlineKeyboardButton("❌ Ні, скасувати", callback_data=f'my_donor_details_{donor_id}')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"⚠️ <b>Підтвердження видалення</b>\n\n"
            f"Даруваник: {donor['donor_name']}\n"
            f"ID: <code>{donor['donor_tango_id']}</code>\n\n"
            f"Ви впевнені?"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @mentor_or_higher
    async def delete_donor(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                          donor_id: int, user_role=None, user_data=None):
        """Видаляє даруваника"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        donors = self.bot.db.get_user_donors(user_id)
        donor = next((d for d in donors if d['id'] == donor_id), None)
        
        if not donor:
            await query.answer("❌ Даруваника не знайдено", show_alert=True)
            return
        
        success = self.bot.db.delete_user_donor(donor_id)
        
        if success:
            # Логування
            self.bot.db.add_audit_log(
                user_telegram_id=user_id,
                user_name=user_data.get('full_name', ''),
                action_type='delete_donor',
                target_type='user_donor',
                target_id=str(donor_id),
                target_name=donor['donor_name'],
                details={'tango_id': donor['donor_tango_id']}
            )
            
            await query.answer("✅ Даруваника видалено", show_alert=True)
            await self.show_my_donors_list(update, context, 0, user_role, user_data)
        else:
            await query.answer("❌ Помилка при видаленні", show_alert=True)
    
    # ================================
    # ПОШУК ДАРУВАНИКІВ
    # ================================
    
    @mentor_or_higher
    async def start_search_donors(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 user_role=None, user_data=None):
        """Початок пошуку даруваників"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        self.bot.temp_data[user_id] = {
            'action': 'searching_personal_donors',
            'step': 'enter_query'
        }
        
        keyboard = [[InlineKeyboardButton("❌ Скасувати", callback_data='my_donors_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔍 <b>Пошук даруваників</b>\n\n"
            "Надішліть ім'я або ID для пошуку:"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @mentor_or_higher
    async def process_search_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  user_role=None, user_data=None):
        """Обробка пошукового запиту"""
        user_id = update.effective_user.id
        
        # Перевіряємо чи є активний процес
        if (user_id not in self.bot.temp_data or 
            self.bot.temp_data[user_id].get('action') != 'searching_personal_donors'):
            return
        
        search_query = update.message.text.strip()
        
        results = self.bot.db.search_user_donor(user_id, search_query)
        
        if not results:
            keyboard = [
                [InlineKeyboardButton("🔍 Новий пошук", callback_data='my_donors_search')],
                [InlineKeyboardButton("◀️ Назад", callback_data='my_donors_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🔍 Пошук: <code>{search_query}</code>\n\n"
                f"📭 Нічого не знайдено",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            text = f"🔍 Пошук: <code>{search_query}</code>\n\n📊 Знайдено: {len(results)}\n\n"
            
            keyboard = []
            for donor in results:
                donor_name = donor['donor_name']
                donor_id_short = donor['donor_tango_id'][:10] + '...' if len(donor['donor_tango_id']) > 10 else donor['donor_tango_id']
                keyboard.append([
                    InlineKeyboardButton(
                        f"{donor_name} ({donor_id_short})",
                        callback_data=f'my_donor_details_{donor["id"]}'
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("🔍 Новий пошук", callback_data='my_donors_search'),
                InlineKeyboardButton("◀️ Назад", callback_data='my_donors_menu')
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        # Очищаємо temp_data
        del self.bot.temp_data[user_id]
    
    # ================================
    # ВЛАСНИК: ВСІ ДАРУВАНИКИ КОРИСТУВАЧІВ
    # ================================
    
    @owner_only
    async def show_all_users_donors(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   user_role=None, user_data=None):
        """Показує всіх даруваників всіх користувачів (тільки Власник)"""
        query = update.callback_query
        await query.answer()
        
        all_donors = self.bot.db.get_all_user_donors_grouped()
        
        if not all_donors:
            text = "👥 <b>Всі даруваники користувачів</b>\n\n📭 Список порожній"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='my_donors_menu')]]
        else:
            total_donors = sum(len(donors) for donors in all_donors.values())
            text = f"👥 <b>Всі даруваники користувачів</b>\n\n📊 Користувачів: {len(all_donors)}\n💝 Всього даруваників: {total_donors}\n\n"
            
            keyboard = []
            for user_id, donors in all_donors.items():
                user_name = donors[0]['user_name'] if donors else f"ID: {user_id}"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{user_name} ({len(donors)} даруваників)",
                        callback_data=f'view_user_donors_{user_id}'
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='my_donors_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДОПОМІЖНІ МЕТОДИ
    # ================================
    
    def _extract_tango_id(self, text: str) -> str:
        """Витягує Tango ID з посилання або тексту"""
        # Пошук в URL
        match = re.search(r'tango\.me/([a-zA-Z0-9_-]+)', text)
        if match:
            return match.group(1)
        
        # Якщо просто username
        if re.match(r'^[a-zA-Z0-9_-]+$', text):
            return text
        
        return None
