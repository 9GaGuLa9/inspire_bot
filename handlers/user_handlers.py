# user_handlers.py
# Обробники для управління користувачами бота

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from role_decorators import *
import config

logger = logging.getLogger(__name__)


class UserHandlers:
    """Клас для обробки операцій з користувачами"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ================================
    # ГОЛОВНЕ МЕНЮ КОРИСТУВАЧІВ
    # ================================
    
    @admin_or_higher
    async def show_users_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             user_role=None, user_data=None):
        """Показує меню управління користувачами"""
        query = update.callback_query
        if query:
            await query.answer()
        
        keyboard = []
        
        # Власник може керувати всіма
        if user_role == 'owner':
            keyboard.extend([
                [InlineKeyboardButton("⭐ Суперадміни", callback_data='users_list_superadmin')],
                [InlineKeyboardButton("🔷 Адміни", callback_data='users_list_admin')],
                [InlineKeyboardButton("🎯 Ментори", callback_data='users_list_mentor')],
                [InlineKeyboardButton("👤 Гості", callback_data='users_list_guest')],
                [InlineKeyboardButton("➕ Додати користувача", callback_data='users_add')],
            ])
        
        # Суперадмін може керувати адмінами, менторами, гостями
        elif user_role == 'superadmin':
            keyboard.extend([
                [InlineKeyboardButton("🔷 Адміни", callback_data='users_list_admin')],
                [InlineKeyboardButton("🎯 Ментори", callback_data='users_list_mentor')],
                [InlineKeyboardButton("👤 Гості", callback_data='users_list_guest')],
                [InlineKeyboardButton("➕ Додати користувача", callback_data='users_add')],
            ])
        
        # Адмін може керувати менторами та гостями
        elif user_role == 'admin':
            keyboard.extend([
                [InlineKeyboardButton("🎯 Ментори", callback_data='users_list_mentor')],
                [InlineKeyboardButton("👤 Гості", callback_data='users_list_guest')],
                [InlineKeyboardButton("➕ Додати користувача", callback_data='users_add')],
            ])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='main_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "👥 <b>Управління користувачами</b>\n\nОберіть дію:"
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # СПИСОК КОРИСТУВАЧІВ
    # ================================
    
    @admin_or_higher
    async def show_users_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             role_filter: str, user_role=None, user_data=None):
        """Показує список користувачів за роллю"""
        query = update.callback_query
        await query.answer()
        
        # Перевірка доступу
        if not can_manage_role(user_role, role_filter):
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        users = self.bot.db.get_all_users(role=role_filter)
        
        role_emoji = config.ROLE_EMOJI.get(role_filter, '👤')
        role_name = config.ROLES.get(role_filter, role_filter)
        
        if not users:
            text = f"{role_emoji} <b>{role_name}</b>\n\n📭 Список порожній"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='users_menu')]]
        else:
            text = f"{role_emoji} <b>{role_name}</b>\n\n"
            keyboard = []
            
            for user in users:
                user_name = user.get('full_name') or user.get('username') or f"ID: {user['telegram_id']}"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{user_name}",
                        callback_data=f'user_details_{user["telegram_id"]}'
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='users_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДЕТАЛІ КОРИСТУВАЧА
    # ================================
    
    @admin_or_higher
    async def show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               target_telegram_id: int, user_role=None, user_data=None):
        """Показує детальну інформацію про користувача"""
        query = update.callback_query
        await query.answer()
        
        user = self.bot.db.get_user_by_telegram_id(target_telegram_id)
        
        if not user:
            await query.answer("❌ Користувача не знайдено", show_alert=True)
            return
        
        # Перевірка доступу
        if not can_manage_role(user_role, user['role']):
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        role_emoji = config.ROLE_EMOJI.get(user['role'], '👤')
        role_name = config.ROLES.get(user['role'], user['role'])
        
        text = (
            f"{role_emoji} <b>{user.get('full_name', 'N/A')}</b>\n\n"
            f"🆔 Telegram ID: <code>{user['telegram_id']}</code>\n"
            f"👤 Username: @{user.get('username', 'N/A')}\n"
            f"💼 Роль: {role_name}\n"
            f"📅 Доданий: {user['created_at'][:10]}\n"
        )
        
        # Додаткова статистика для менторів
        if user['role'] == 'mentor':
            # Отримуємо ID ментора з таблиці mentors
            mentor = self.bot.db.get_mentor_by_telegram_id(target_telegram_id)
            if mentor:
                streamers = self.bot.db.get_streamers_by_mentor(mentor['id'])
                active_streamers = [s for s in streamers if s.get('is_active')]
                text += f"\n📊 Стрімерів: {len(streamers)} (активних: {len(active_streamers)})"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Змінити роль", callback_data=f'user_change_role_{target_telegram_id}')],
            [InlineKeyboardButton("🗑 Деактивувати", callback_data=f'user_deactivate_{target_telegram_id}')],
            [InlineKeyboardButton("◀️ Назад", callback_data=f'users_list_{user["role"]}')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДОДАВАННЯ КОРИСТУВАЧА
    # ================================
    
    @admin_or_higher
    async def start_add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                            user_role=None, user_data=None):
        """Початок процесу додавання користувача"""
        query = update.callback_query
        await query.answer()
        
        # Визначаємо які ролі може додавати поточний користувач
        available_roles = []
        if user_role == 'owner':
            available_roles = ['superadmin', 'admin', 'mentor', 'guest']
        elif user_role == 'superadmin':
            available_roles = ['admin', 'mentor', 'guest']
        elif user_role == 'admin':
            available_roles = ['mentor', 'guest']
        
        if not available_roles:
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        # Зберігаємо етап в temp_data
        user_id = update.effective_user.id
        self.bot.temp_data[user_id] = {
            'action': 'adding_user',
            'available_roles': available_roles,
            'step': 'select_role'
        }
        
        keyboard = []
        for role in available_roles:
            role_emoji = config.ROLE_EMOJI.get(role, '👤')
            role_name = config.ROLES.get(role, role)
            keyboard.append([
                InlineKeyboardButton(
                    f"{role_emoji} {role_name}",
                    callback_data=f'user_add_role_{role}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data='users_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "➕ <b>Додавання користувача</b>\n\nКрок 1: Оберіть роль:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def select_role_for_new_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      role: str, user_role=None, user_data=None):
        """Вибір ролі для нового користувача"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Перевіряємо чи може додавати цю роль
        if not can_manage_role(user_role, role):
            await query.answer("❌ Немає доступу до цієї ролі", show_alert=True)
            return
        
        # Оновлюємо temp_data
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        
        self.bot.temp_data[user_id].update({
            'action': 'adding_user',
            'role': role,
            'step': 'enter_telegram_id'
        })
        
        role_emoji = config.ROLE_EMOJI.get(role, '👤')
        role_name = config.ROLES.get(role, role)
        
        keyboard = [[InlineKeyboardButton("❌ Скасувати", callback_data='users_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"➕ <b>Додавання користувача</b>\n\n"
            f"Роль: {role_emoji} {role_name}\n\n"
            f"Крок 2: Надішліть Telegram ID нового користувача\n\n"
            f"💡 Щоб отримати ID, користувач повинен написати /start боту"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def process_new_user_telegram_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                           user_role=None, user_data=None):
        """Обробка введеного Telegram ID"""
        user_id = update.effective_user.id
        
        # Перевіряємо чи є активний процес додавання
        if user_id not in self.bot.temp_data or self.bot.temp_data[user_id].get('action') != 'adding_user':
            return
        
        try:
            new_telegram_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Невірний формат. Надішліть числовий Telegram ID.")
            return
        
        # Перевіряємо чи користувач вже існує
        existing_user = self.bot.db.get_user_by_telegram_id(new_telegram_id)
        if existing_user:
            await update.message.reply_text(
                f"❌ Користувач з ID {new_telegram_id} вже існує в системі!\n"
                f"Роль: {config.ROLES.get(existing_user['role'], existing_user['role'])}"
            )
            del self.bot.temp_data[user_id]
            return
        
        # Зберігаємо telegram_id
        self.bot.temp_data[user_id]['new_telegram_id'] = new_telegram_id
        self.bot.temp_data[user_id]['step'] = 'enter_full_name'
        
        keyboard = [[InlineKeyboardButton("❌ Скасувати", callback_data='users_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ ID: <code>{new_telegram_id}</code>\n\n"
            f"Крок 3: Надішліть ПІБ користувача:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    @admin_or_higher
    async def process_new_user_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        user_role=None, user_data=None):
        """Обробка введеного ПІБ та створення користувача"""
        user_id = update.effective_user.id
        
        # Перевіряємо чи є активний процес додавання
        if (user_id not in self.bot.temp_data or 
            self.bot.temp_data[user_id].get('action') != 'adding_user' or
            self.bot.temp_data[user_id].get('step') != 'enter_full_name'):
            return
        
        full_name = update.message.text.strip()
        temp_data = self.bot.temp_data[user_id]
        
        # Створюємо користувача
        new_telegram_id = temp_data['new_telegram_id']
        role = temp_data['role']
        
        user_db_id = self.bot.db.add_user(
            telegram_id=new_telegram_id,
            username='',  # Буде оновлено при першому /start
            full_name=full_name,
            role=role,
            created_by=user_id
        )
        
        if user_db_id:
            # Логування в аудит
            self.bot.db.add_audit_log(
                user_telegram_id=user_id,
                user_name=user_data.get('full_name', ''),
                action_type='add_user',
                target_type='user',
                target_id=str(new_telegram_id),
                target_name=full_name,
                details={'role': role}
            )
            
            # Сповіщення новому користувачу
            await self.bot.notification_service.notify_new_user_role(
                telegram_id=new_telegram_id,
                role=role,
                assigned_by=user_data.get('full_name', 'Адміністратор')
            )
            
            role_emoji = config.ROLE_EMOJI.get(role, '👤')
            role_name = config.ROLES.get(role, role)
            
            keyboard = [[InlineKeyboardButton("◀️ До користувачів", callback_data='users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ <b>Користувача додано!</b>\n\n"
                f"👤 {full_name}\n"
                f"🆔 ID: <code>{new_telegram_id}</code>\n"
                f"💼 Роль: {role_emoji} {role_name}\n\n"
                f"Користувачу надіслано сповіщення.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ Помилка при додаванні користувача")
        
        # Очищаємо temp_data
        del self.bot.temp_data[user_id]
    
    # ================================
    # ЗМІНА РОЛІ
    # ================================
    
    @admin_or_higher
    async def start_change_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               target_telegram_id: int, user_role=None, user_data=None):
        """Початок процесу зміни ролі"""
        query = update.callback_query
        await query.answer()
        
        target_user = self.bot.db.get_user_by_telegram_id(target_telegram_id)
        
        if not target_user or not can_manage_role(user_role, target_user['role']):
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        # Визначаємо доступні ролі
        available_roles = []
        if user_role == 'owner':
            available_roles = ['superadmin', 'admin', 'mentor', 'guest']
        elif user_role == 'superadmin':
            available_roles = ['admin', 'mentor', 'guest']
        elif user_role == 'admin':
            available_roles = ['mentor', 'guest']
        
        # Видаляємо поточну роль зі списку
        if target_user['role'] in available_roles:
            available_roles.remove(target_user['role'])
        
        keyboard = []
        for role in available_roles:
            role_emoji = config.ROLE_EMOJI.get(role, '👤')
            role_name = config.ROLES.get(role, role)
            keyboard.append([
                InlineKeyboardButton(
                    f"{role_emoji} {role_name}",
                    callback_data=f'user_set_role_{target_telegram_id}_{role}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data=f'user_details_{target_telegram_id}')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_role_emoji = config.ROLE_EMOJI.get(target_user['role'], '👤')
        current_role_name = config.ROLES.get(target_user['role'], target_user['role'])
        
        text = (
            f"🔄 <b>Зміна ролі</b>\n\n"
            f"Користувач: {target_user.get('full_name', 'N/A')}\n"
            f"Поточна роль: {current_role_emoji} {current_role_name}\n\n"
            f"Оберіть нову роль:"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def confirm_change_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 target_telegram_id: int, new_role: str, 
                                 user_role=None, user_data=None):
        """Підтвердження та виконання зміни ролі"""
        query = update.callback_query
        await query.answer()
        
        target_user = self.bot.db.get_user_by_telegram_id(target_telegram_id)
        
        if not target_user or not can_manage_role(user_role, target_user['role']):
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        old_role = target_user['role']
        
        # Оновлюємо роль
        success = self.bot.db.update_user_role(target_telegram_id, new_role)
        
        if success:
            # Логування
            self.bot.db.add_audit_log(
                user_telegram_id=user_data['telegram_id'],
                user_name=user_data.get('full_name', ''),
                action_type='role_change',
                target_type='user',
                target_id=str(target_telegram_id),
                target_name=target_user.get('full_name', ''),
                details={'old_role': old_role, 'new_role': new_role}
            )
            
            # Сповіщення користувачу
            await self.bot.notification_service.notify_user_role_changed(
                telegram_id=target_telegram_id,
                old_role=old_role,
                new_role=new_role,
                changed_by=user_data.get('full_name', 'Адміністратор')
            )
            
            await query.answer("✅ Роль змінено!", show_alert=True)
            
            # Повертаємося до деталей користувача
            await self.show_user_details(update, context, target_telegram_id, user_role, user_data)
        else:
            await query.answer("❌ Помилка при зміні ролі", show_alert=True)
    
    # ================================
    # ДЕАКТИВАЦІЯ КОРИСТУВАЧА
    # ================================
    
    @admin_or_higher
    async def deactivate_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             target_telegram_id: int, user_role=None, user_data=None):
        """Деактивує користувача"""
        query = update.callback_query
        await query.answer()
        
        target_user = self.bot.db.get_user_by_telegram_id(target_telegram_id)
        
        if not target_user or not can_manage_role(user_role, target_user['role']):
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ Так, деактивувати", callback_data=f'user_deactivate_confirm_{target_telegram_id}')],
            [InlineKeyboardButton("❌ Ні, скасувати", callback_data=f'user_details_{target_telegram_id}')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"⚠️ <b>Підтвердження деактивації</b>\n\n"
            f"Користувач: {target_user.get('full_name', 'N/A')}\n"
            f"Роль: {config.ROLES.get(target_user['role'], target_user['role'])}\n\n"
            f"Ви впевнені?"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def confirm_deactivate_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     target_telegram_id: int, user_role=None, user_data=None):
        """Підтвердження деактивації"""
        query = update.callback_query
        await query.answer()
        
        target_user = self.bot.db.get_user_by_telegram_id(target_telegram_id)
        
        if not target_user or not can_manage_role(user_role, target_user['role']):
            await query.answer("❌ Немає доступу", show_alert=True)
            return
        
        success = self.bot.db.delete_user(target_telegram_id)
        
        if success:
            # Логування
            self.bot.db.add_audit_log(
                user_telegram_id=user_data['telegram_id'],
                user_name=user_data.get('full_name', ''),
                action_type='delete_user',
                target_type='user',
                target_id=str(target_telegram_id),
                target_name=target_user.get('full_name', ''),
                details={'role': target_user['role']}
            )
            
            # Сповіщення користувачу
            await self.bot.notification_service.notify_user_deactivated(
                telegram_id=target_telegram_id,
                deactivated_by=user_data.get('full_name', 'Адміністратор')
            )
            
            await query.answer("✅ Користувача деактивовано", show_alert=True)
            
            # Повертаємося до списку
            await self.show_users_list(update, context, target_user['role'], user_role, user_data)
        else:
            await query.answer("❌ Помилка при деактивації", show_alert=True)
