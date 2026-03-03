"""
Handler'и для керування користувачами бота (система ролей)
"""
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from html import escape as html_escape
from config import ROLES, ROLE_EMOJI, OWNER_ID


class BotUsersHandlers:
    """Обробка операцій з користувачами бота"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def show_bot_users_menu(self, query, user_id):
        """Меню керування користувачами бота"""
        users_count = len(self.bot.db.get_all_bot_users())
        
        keyboard = [
            [InlineKeyboardButton("➕ Додати користувача", callback_data='add_bot_user')],
            [InlineKeyboardButton("📋 Список користувачів", callback_data='list_bot_users')],
            [InlineKeyboardButton("✏️ Змінити роль", callback_data='change_user_role_select')],
            [InlineKeyboardButton("➖ Видалити користувача", callback_data='delete_bot_user_select')],
            [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👤 **Керування користувачами**\n\nВсього користувачів: {users_count}\n\nОберіть дію:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_users_list(self, query):
        """Показати список всіх користувачів"""
        users = self.bot.db.get_all_bot_users()
        
        if not users:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Список користувачів порожній!",
                reply_markup=reply_markup
            )
            return
        
        # Використовуємо HTML і екранівку для динамічних полів
        text = f"📋 <b>Список користувачів</b> ({len(users)}):\n\n"
        
        for user_data in users:
            telegram_id, username, role, status, created_at = user_data
            
            emoji = ROLE_EMOJI.get(role, '👤')
            role_name = ROLES.get(role, role)
            
            # Статус emoji
            status_emoji = '✅' if status == 'active' else '🔔' if status == 'pending' else '❌'
            status_name = 'Активний' if status == 'active' else 'Очікує' if status == 'pending' else 'Неактивний'
            
            # Escape values
            display_username = html_escape(username) if username else 'Без username'
            display_id = html_escape(str(telegram_id)) if telegram_id is not None else 'Очікується'
            display_role = html_escape(role_name)
            display_status_name = html_escape(status_name)

            text += f"{emoji} <b>{display_username}</b>\n"
            text += f"   ID: <code>{display_id}</code>\n"
            text += f"   Роль: {display_role}\n"
            text += f"   Статус: {status_emoji} {display_status_name}\n"
            
            if telegram_id is not None and telegram_id == OWNER_ID:
                text += f"   👑 Власник\n"
            
            text += f"\n"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Failed to send HTML-formatted users list: {e}. Falling back to plain text.")
            await query.edit_message_text(
                textplain := text.replace('<b>', '').replace('</b>', '').replace('<code>', '`').replace('</code>', '`'),
                reply_markup=reply_markup
            )
    
    async def start_add_user(self, query, user_id):
        """Початок додавання користувача"""
        self.bot.user_states[user_id] = 'waiting_new_user_username'
        
        await query.edit_message_text(
            "➕ **Додавання користувача**\n\n"
            "НадішлітьUsername користувача (напр. `@username`):",
            parse_mode='Markdown'
        )
    
    async def process_new_user_username(self, update, text, user_id):
        username = text.strip()
        if username.startswith('@'):
            username = username[1:]

        if not username or len(username) < 3:
            await update.message.reply_text("❌ Некоректний username! Мінімум 3 символи.")
            return

        # ДОДАНО: перевірка чи username вже існує в bot_users
        existing = self.bot.db.get_bot_user_by_username(username)
        if existing:
            from config import ROLES, ROLE_EMOJI
            role_name = ROLES.get(existing['role'], existing['role'])
            emoji = ROLE_EMOJI.get(existing['role'], '👤')
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"⚠️ Користувач @{username} вже є в системі!\n\n"
                f"Роль: {emoji} {role_name}\n"
                f"Статус: {existing.get('status', '—')}\n\n"
                f"Якщо потрібно змінити роль — скористайтесь функцією редагування.",
                reply_markup=reply_markup
            )
            return
        
        # Зберігаємо username і просимо вибрати роль
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['new_user_username'] = username
        
        # Логування для діагностики
        logging.info(f"process_new_user_username: user_id={user_id} username_for_new={username}")

        # Показуємо вибір ролі
        await self.show_role_selection_for_new_user(update, user_id, username)
    
    async def show_role_selection_for_new_user(self, update, user_id, username):
        """Показати вибір ролі для нового користувача"""
        current_user_role = self.bot.db.get_user_role(user_id)

        # Логування для діагностики проблем з ролями
        logging.info(f"show_role_selection_for_new_user: user_id={user_id} current_user_role={current_user_role} username={username}")

        keyboard = []

        # Якщо роль не знайдена або користувач не має доступу - показуємо повідомлення і повертаємось
        if not current_user_role:
            # Якщо користувач - власник (OWNER_ID), можливо він ще не доданий у базу → встановимо роль owner
            if user_id == OWNER_ID:
                current_user_role = 'owner'
                logging.info(f"User {user_id} is OWNER_ID: treating as 'owner' for role selection")
                try:
                    # Додамо у базу, якщо його ще немає
                    self.bot.db.add_bot_user(user_id, None, 'owner', user_id)
                except Exception:
                    logging.exception("Failed to add OWNER to bot_users")
            else:
                try:
                    await update.message.reply_text(
                        "❌ У вас немає прав для додавання користувача або роль не знайдена в системі. Зверніться до власника бота.")
                except Exception:
                    # Якщо це CallbackQuery (update.callback_query), відповідаємо через edit_message_text
                    try:
                        await update.callback_query.edit_message_text(
                            "❌ У вас немає прав для додавання користувача або роль не знайдена в системі. Зверніться до власника бота.")
                    except Exception:
                        logging.exception("Failed to send access denied message in show_role_selection_for_new_user")
                return

        # Формуємо список доступних ролей на основі поточної ролі (логіка та ж, що в user_handlers.start_add_user)
        available_roles = []
        if current_user_role == 'owner':
            available_roles = ['superadmin', 'admin', 'mentor', 'guest']
        elif current_user_role == 'superadmin':
            available_roles = ['admin', 'mentor', 'guest']
        elif current_user_role == 'admin':
            available_roles = ['mentor', 'guest']

        if not available_roles:
            # Якщо у користувача нема доступних ролей для створення — інформуємо
            try:
                await update.message.reply_text("❌ Немає доступних ролей для призначення. Зверніться до адміністратора.")
            except Exception:
                try:
                    await update.callback_query.edit_message_text(
                        "❌ Немає доступних ролей для призначення. Зверніться до адміністратора.")
                except Exception:
                    logging.exception("Failed to send no available roles message")
            return

        # Додаємо кнопки для доступних ролей
        for role in available_roles:
            role_name = ROLES.get(role, role)
            emoji = ROLE_EMOJI.get(role, '👤')
            callback_data = f'select_role_{role}|{username}'
            keyboard.append([InlineKeyboardButton(f"{emoji} {role_name}", callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data='bot_users_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Формуємо повідомлення в HTML, екранівка username
        esc_username = html_escape(username)
        text_html = (
            f"👤 <b>Вибір ролі</b>\n\n"
            f"Username: <code>@{esc_username}</code>\n\n"
            f"Оберіть роль:"
        )

        try:
            await update.message.reply_text(
                text_html,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Failed to send HTML role selection: {e}. Fallback to plain text.")
            await update.message.reply_text(
                f"👤 Вибір ролі\n\nUsername: @{username}\n\nОберіть роль:",
                reply_markup=reply_markup
            )
    
    async def show_role_selection(self, update, user_id, target_user_id, is_new=True):
        """Показати вибір ролі"""
        current_user_role = self.bot.db.get_user_role(user_id)
        logging.info(f"show_role_selection: user_id={user_id} role={current_user_role} target_user_id={target_user_id}")
        
        keyboard = []
        
        # Якщо роль відсутня → інформуємо користувача
        if not current_user_role:
            try:
                if update.callback_query:
                    await update.callback_query.answer("❌ У вас немає прав для зміни ролей або роль не знайдена в системі", show_alert=True)
                else:
                    await update.message.reply_text("❌ У вас немає прав для зміни ролей або роль не знайдена в системі")
            except Exception:
                logging.exception("Failed to send access denied in show_role_selection")
            return

        # Власник може призначати всі ролі
        if current_user_role == 'owner':
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['superadmin']} Суперадмін", 
                callback_data=f'set_role_superadmin_{target_user_id}'
            )])
        
        # Власник і Суперадмін можуть призначати Адміна
        if current_user_role in ['owner', 'superadmin']:
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['admin']} Адмін", 
                callback_data=f'set_role_admin_{target_user_id}'
            )])
        
        # Адміни і вище можуть призначати Ментора і Гостя
        if current_user_role in ['owner', 'superadmin', 'admin']:
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['mentor']} Ментор", 
                callback_data=f'set_role_mentor_{target_user_id}'
            )])
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['guest']} Гість", 
                callback_data=f'set_role_guest_{target_user_id}'
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Скасувати", callback_data='bot_users_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"👤 {'**Додавання користувача**' if is_new else '**Зміна ролі**'}\n\n"
        text += f"ID: `{target_user_id}`\n\n"
        text += "Оберіть роль:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def confirm_role_and_send_invite(self, query, user_id, role, username):
        """Підтвердження ролі та питання про відправку запрошення"""
        role_name = ROLES.get(role, role)
        emoji = ROLE_EMOJI.get(role, '👤')
        
        # Зберігаємо дані
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['pending_username'] = username
        self.bot.temp_data[user_id]['pending_role'] = role
        
        keyboard = [
            [InlineKeyboardButton("✅ Так, надіслати", callback_data=f'send_invite_{username}|{role}')],
            [InlineKeyboardButton("❌ Ні, додати без запрошення", callback_data=f'skip_invite_{username}|{role}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👤 **Підтвердження**\n\n"
            f"Username: `@{username}`\n"
            f"Роль: {emoji} {role_name}\n\n"
            f"Надіслати запрошення користувачу?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def send_invite_to_user(self, query, user_id, username, role):
        """Генерує і надсилає запрошення користувачу"""
        import uuid

        # Генеруємо activation code
        activation_code = str(uuid.uuid4()).replace('-', '')[:16]

        # Перевіряємо, чи такий username вже існує
        existing = self.bot.db.get_bot_user_by_username(username)
        if existing:
            await query.edit_message_text(
                "❌ Користувач з таким username вже існує в системі!"
            )
            return

        # Додаємо користувача в БД зі статусом pending
        success = self.bot.db.add_bot_user_pending(username, role, user_id, activation_code)

        if not success:
            await query.edit_message_text(
                "❌ Помилка при додаванні користувача!"
            )
            return

        # Генеруємо посилання активації
        activation_link = f"https://t.me/{self.bot.application.bot.username}?start=activate_{activation_code}"

        role_name = ROLES.get(role, role)
        emoji = ROLE_EMOJI.get(role, '👤')

        # Показуємо адміну посилання для копіювання
        try:
            # Екраніруємо дані для HTML
            esc_username = html_escape(f"@{username}")
            esc_activation_code = html_escape(activation_code)
            esc_role_name = html_escape(role_name)

            invite_text = (
                f"👋 <b>Добро пожаловать!</b>\n\n"
                f"Вам надано роль: {emoji} {esc_role_name}\n\n"
                f"Щоб активувати доступ, перейдіть за посиланням:\n"
                f"{activation_link}\n\n"
                f"Або натисніть кнопку активації у боті."
            )

            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Формуємо повідомлення в HTML і екрануємо динамічні поля
            message_text = (
                f"✅ <b>Запрошення готово!</b>\n\n"
                f"Username: <code>{esc_username}</code>\n"
                f"Роль: {emoji} {esc_role_name}\n"
                f"Статус: 🔔 Очікує активації (pending)\n"
                f"Activation code: <code>{esc_activation_code}</code>\n\n"
                f"<b>Посилання для відправки користувачу:</b>\n<a href=\"{activation_link}\">{activation_link}</a>\n\n"
                f"<i>Скопіюйте це посилання і надішліть користувачу</i>"
            )

            try:
                await query.edit_message_text(
                    message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.error(f"Failed to send HTML message, fallback to plain text. Error: {e}")
                await query.edit_message_text(
                    f"✅ Запрошення готово!\n\nUsername: @{username}\nРоль: {emoji} {role_name}\nАктивуйте: {activation_link}",
                    reply_markup=reply_markup
                )
        except Exception as e:
            logging.error(f"Error sending invite: {e}")
            await query.edit_message_text(
                f"❌ Помилка при відправці запрошення: {e}"
            )

        # Очищаємо стан
        self.bot.user_states.pop(user_id, None)
        self.bot.temp_data.pop(user_id, None)

    async def add_user_without_invite(self, query, user_id, username, role):
        """Додає користувача без запрошення (статус inactive)"""
        # Додаємо користувача в БД зі статусом inactive
        # Перевіряємо дублікати
        existing = self.bot.db.get_bot_user_by_username(username)
        if existing:
            await query.edit_message_text(
                "❌ Користувач з таким username вже існує в системі!"
            )
            return

        success = self.bot.db.add_bot_user_by_username(username, role, user_id, status='inactive')
        
        if success:
            role_name = ROLES.get(role, role)
            emoji = ROLE_EMOJI.get(role, '👤')
            
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # повідомлення в HTML (з екранівкою)
            esc_username = html_escape(f"@{username}")
            esc_role_name = html_escape(role_name)
            message_text = (
                f"✅ <b>Користувача додано!</b>\n\n"
                f"Username: <code>{esc_username}</code>\n"
                f"Роль: {emoji} {esc_role_name}\n"
                f"Статус: ❌ Неактивний (без запрошення)\n\n"
                f"<i>Запрошення можна надіслати пізніше</i>"
            )
            try:
                await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='HTML')
            except Exception:
                logging.exception("Failed to send add_user_without_invite HTML message")
                await query.edit_message_text(
                    f"✅ Користувача додано!\nUsername: @{username}\nРоль: {emoji} {role_name}\nСтатус: Неактивний",
                    reply_markup=reply_markup
                )
            
            # Очищаємо стан
            self.bot.user_states.pop(user_id, None)
            self.bot.temp_data.pop(user_id, None)
        else:
            await query.edit_message_text(
                "❌ Помилка при додаванні користувача!"
            )
    
    async def handle_user_activation(self, update, activation_code):
        """Обробка активації користувача за кодом"""
        user_id = update.message.from_user.id
        
        # Активуємо користувача
        success = self.bot.db.activate_bot_user(activation_code, user_id)
        
        if success:
            user = self.bot.db.get_bot_user_by_telegram_id(user_id)
            role_name = ROLES.get(user['role'], user['role'])
            emoji = ROLE_EMOJI.get(user['role'], '👤')
            
            await update.message.reply_text(
                f"✅ **Активацію успішно!**\n\n"
                f"Ваша роль: {emoji} {role_name}\n\n"
                f"Тепер у вас є повний доступ до бота.",
                parse_mode='Markdown'
            )
            
            # Показуємо головне меню
            from config import ROLE_HIERARCHY
            await self.bot.menu_handlers.show_start_menu_with_role(update, None, user['role'])
        else:
            await update.message.reply_text(
                "❌ Помилка активації!\n\n"
                "Код активації невірний або вже використаний.\n"
                "Зверніться до адміністратора.",
                parse_mode='Markdown'
            )
    
    async def assign_role(self, query, user_id, role, target_user_id):
        """Призначити роль користувачу"""
        username = query.from_user.username
        
        # Додаємо користувача
        success = self.bot.db.add_bot_user(target_user_id, None, role, user_id)
        
        if success:
            role_name = ROLES.get(role, role)
            emoji = ROLE_EMOJI.get(role, '👤')
            
            await query.edit_message_text(
                f"✅ **Користувача додано!**\n\n"
                f"ID: `{target_user_id}`\n"
                f"Роль: {emoji} {role_name}",
                parse_mode='Markdown'
            )
            
            # Очищаємо стан
            self.bot.user_states.pop(user_id, None)
            self.bot.temp_data.pop(user_id, None)
        else:
            await query.edit_message_text(
                "❌ Помилка при додаванні користувача!"
            )
    
    async def show_users_for_role_change(self, query):
        """Показати список користувачів для зміни ролі"""
        users = self.bot.db.get_all_bot_users()
        
        if not users:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Список користувачів порожній!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for user_data in users:
            telegram_id, username, role, status, created_at = user_data
            
            # Не показуємо власника
            if telegram_id == OWNER_ID:
                continue
            
            emoji = ROLE_EMOJI.get(role, '👤')
            status_emoji = '✅' if status == 'active' else '🔔' if status == 'pending' else '❌'
            display_name = username or f"ID: {telegram_id or 'Очікується'}"
            
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {display_name} {status_emoji}",
                callback_data=f'change_role_{telegram_id}' if telegram_id else f'change_role_inactive_{username}'
            )])
        
        # Якщо після фільтрації список порожній
        if not keyboard:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Немає доступних користувачів для зміни ролі!",
                reply_markup=reply_markup
            )
            return
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✏️ **Зміна ролі**\n\nОберіть користувача:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def change_user_role(self, query, user_id, target_user_id):
        """Змінити роль користувача за telegram_id"""
        target_user = self.bot.db.get_bot_user_by_telegram_id(target_user_id)
        
        if not target_user:
            await query.edit_message_text("❌ Користувача не знайдено!")
            return
        
        await self._show_role_selection(query, user_id, target_user_id, target_user)
    
    async def change_user_role_by_username(self, query, user_id, username):
        """Змінити роль користувача за username"""
        try:
            logging.info(f"change_user_role_by_username called for username: {username}")
            target_user = self.bot.db.get_bot_user_by_username(username)
            logging.info(f"Found target_user: {target_user}")
            
            if not target_user:
                await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            await self._show_role_selection(query, user_id, target_user['telegram_id'], target_user)
        except Exception as e:
            logging.error(f"Error in change_user_role_by_username: {e}")
            await query.answer(f"❌ Помилка: {e}", show_alert=True)
    
    async def _show_role_selection(self, query, user_id, target_user_id, target_user):
        """Показати вибір нової ролі"""
        # Получаємо роль поточного користувача
        current_user_role = self.bot.db.get_user_role(user_id)
        
        keyboard = []
        
        # Якщо це неактивний користувач (без telegram_id), використовуємо username в callback_data
        is_inactive = target_user_id is None or target_user_id == ''
        username = target_user.get('username', '')
        
        # Власник може змінювати всі ролі
        if current_user_role == 'owner':
            if is_inactive:
                callback = f'update_role_superadmin_inactive_{username}'
            else:
                callback = f'update_role_superadmin_{target_user_id}'
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['superadmin']} Суперадмін", 
                callback_data=callback
            )])
        
        # Власник і Суперадмін можуть призначати Адміна
        if current_user_role in ['owner', 'superadmin']:
            if is_inactive:
                callback = f'update_role_admin_inactive_{username}'
            else:
                callback = f'update_role_admin_{target_user_id}'
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['admin']} Адмін", 
                callback_data=callback
            )])
        
        # Адміни і вище можуть призначати Ментора і Гостя
        if current_user_role in ['owner', 'superadmin', 'admin']:
            if is_inactive:
                callback_mentor = f'update_role_mentor_inactive_{username}'
                callback_guest = f'update_role_guest_inactive_{username}'
            else:
                callback_mentor = f'update_role_mentor_{target_user_id}'
                callback_guest = f'update_role_guest_{target_user_id}'
            
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['mentor']} Ментор", 
                callback_data=callback_mentor
            )])
            keyboard.append([InlineKeyboardButton(
                f"{ROLE_EMOJI['guest']} Гість", 
                callback_data=callback_guest
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='change_user_role_select')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_role_emoji = ROLE_EMOJI.get(target_user['role'], '👤')
        current_role_name = ROLES.get(target_user['role'], target_user['role'])
        
        # Формируем текст сообщения безопасно
        message_lines = [
            "✏️ <b>Зміна ролі</b>",
            "",
            f"Користувач: <code>{target_user['username']}</code>"
        ]
        
        if target_user_id:
            message_lines.append(f"ID: <code>{target_user_id}</code>")
        
        message_lines.extend([
            f"Поточна роль: {current_role_emoji} {current_role_name}",
            "",
            "Оберіть нову роль:"
        ])
        
        message_text = "\n".join(message_lines)
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def update_user_role(self, query, new_role, target_user_id):
        """Оновити роль користувача"""
        logging.info(f"update_user_role called: target_user_id={target_user_id} new_role={new_role}")
        success = self.bot.db.update_bot_user_role(target_user_id, new_role)
        
        if success:
            role_name = ROLES.get(new_role, new_role)
            emoji = ROLE_EMOJI.get(new_role, '👤')
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **Роль змінено!**\n\n"
                f"ID: `{target_user_id}`\n"
                f"Нова роль: {emoji} {role_name}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Покажемо більш інформативну помилку
            logging.warning(f"update_user_role failed for id {target_user_id} with role {new_role}")
            await query.edit_message_text("❌ Помилка при зміні ролі! Користувача не знайдено або відсутній telegram_id.")
    
    async def update_user_role_by_username(self, query, new_role, username):
        """Оновити роль користувача за username"""
        try:
            target_user = self.bot.db.get_bot_user_by_username(username)
            if not target_user:
                await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            # Оновлюємо роль (для активних користувачів — по telegram_id, для інактивних — по username)
            if target_user.get('telegram_id'):
                success = self.bot.db.update_bot_user_role(target_user['telegram_id'], new_role)
            else:
                success = self.bot.db.update_bot_user_role_by_username(username, new_role)
            
            if success:
                role_name = ROLES.get(new_role, new_role)
                emoji = ROLE_EMOJI.get(new_role, '👤')
                keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"✅ <b>Роль змінено!</b>\n\n"
                    f"Користувач: <code>{username}</code>\n"
                    f"Нова роль: {emoji} {role_name}",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                logging.warning(f"update_user_role_by_username failed for username {username} new_role {new_role}")
                await query.edit_message_text("❌ Помилка при зміні ролі! Користувача не знайдено або немає telegram_id.")
        except Exception as e:
            logging.error(f"Error in update_user_role_by_username: {e}")
            await query.answer(f"❌ Помилка: {e}", show_alert=True)
    
    async def show_users_for_deletion(self, query):
        """Показати список користувачів для видалення"""
        users = self.bot.db.get_all_bot_users()
        
        if not users:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Список користувачів порожній!",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for user_data in users:
            telegram_id, username, role, status, created_at = user_data
            
            # Не показуємо власника
            if telegram_id == OWNER_ID:
                continue
            
            emoji = ROLE_EMOJI.get(role, '👤')
            status_emoji = '✅' if status == 'active' else '🔔' if status == 'pending' else '❌'
            display_name = username or f"ID: {telegram_id or 'Очікується'}"
            
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {display_name} {status_emoji}",
                callback_data=f'confirm_delete_user_{telegram_id}' if telegram_id else f'confirm_delete_user_inactive_{username}'
            )])
        
        # Якщо після фільтрації список порожній
        if not keyboard:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Немає доступних користувачів для видалення!",
                reply_markup=reply_markup
            )
            return
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➖ **Видалення користувача**\n\nОберіть користувача:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def confirm_delete_user(self, query, target_user_id):
        """Підтвердження видалення користувача за telegram_id"""
        target_user = self.bot.db.get_bot_user_by_telegram_id(target_user_id)
        
        if not target_user:
            await query.edit_message_text("❌ Користувача не знайдено!")
            return
        
        await self._show_delete_confirmation(query, target_user_id, target_user)
    
    async def confirm_delete_user_by_username(self, query, username):
        """Підтвердження видалення користувача за username"""
        try:
            logging.info(f"confirm_delete_user_by_username called for username: {username}")
            target_user = self.bot.db.get_bot_user_by_username(username)
            logging.info(f"Found target_user: {target_user}")
            
            if not target_user:
                await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            await self._show_delete_confirmation(query, target_user['telegram_id'], target_user)
        except Exception as e:
            logging.error(f"Error in confirm_delete_user_by_username: {e}")
            await query.answer(f"❌ Помилка: {e}", show_alert=True)
    
    async def _show_delete_confirmation(self, query, target_user_id, target_user):
        """Показати підтвердження видалення"""
        # Визначаємо callback для підтвердження видалення залежно від доступних ідентифікаторів
        if target_user_id:
            confirm_callback = f'delete_user_confirmed_{target_user_id}'
        else:
            username = target_user.get('username') or ''
            confirm_callback = f'delete_user_confirmed_inactive_{username}'

        keyboard = [
            [InlineKeyboardButton("✅ Так, видалити", callback_data=confirm_callback)],
            [InlineKeyboardButton("❌ Скасувати", callback_data='delete_bot_user_select')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        role_emoji = ROLE_EMOJI.get(target_user['role'], '👤')
        role_name = ROLES.get(target_user['role'], target_user['role'])
        
        # Формируем текст безопасно
        message_lines = [
            "⚠️ <b>Підтвердження видалення</b>",
            "",
            f"Користувач: <code>{target_user['username']}</code>"
        ]
        
        if target_user_id:
            message_lines.append(f"ID: <code>{target_user_id}</code>")
        
        message_lines.extend([
            f"Роль: {role_emoji} {role_name}",
            "",
            "Ви впевнені?"
        ])
        
        message_text = "\n".join(message_lines)
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def delete_user(self, query, target_user_id):
        """Видалити користувача"""
        success = self.bot.db.delete_bot_user(target_user_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"✅ <b>Користувача видалено!</b>\n\n"
                f"ID: <code>{target_user_id}</code>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text("❌ Помилка при видаленні користувача!")
    
    async def delete_user_by_username(self, query, username):
        """Видалити користувача за username"""
        try:
            target_user = self.bot.db.get_bot_user_by_username(username)
            logging.info(f"confirm_delete_user_by_username called for username: {username}")
            logging.info(f"Found target_user: {target_user}")
            if not target_user:
                await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            # Видаляємо або по telegram_id (active) або по username (inactive)
            if target_user.get('telegram_id'):
                success = self.bot.db.delete_bot_user(target_user['telegram_id'])
            else:
                success = self.bot.db.delete_bot_user_by_username(username)

            logging.info(f"delete_user_by_username result for {username}: {success}")
            if success:
                keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='bot_users_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"✅ <b>Користувача видалено!</b>\n\n"
                    f"Користувач: <code>{username}</code>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text("❌ Помилка при видаленні користувача!")
        except Exception as e:
            logging.error(f"Error in delete_user_by_username: {e}")
            await query.answer(f"❌ Помилка: {e}", show_alert=True)
