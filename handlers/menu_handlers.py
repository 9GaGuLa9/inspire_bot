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
        """Показати головне меню"""
        keyboard = [
            [InlineKeyboardButton("👥 База користувачів", callback_data='users_base')],
            [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
            [InlineKeyboardButton("❓ Допомога", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🤖 **Tango Bot**\n\n"
            "Оберіть дію з меню:"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def show_main_menu(self, query):
        """Показати головне меню через callback query"""
        from config import OWNER_ID
        
        user_id = query.from_user.id
        role = self.bot.db.get_user_role(user_id)
        
        # Якщо користувач - власник, але немає в БД
        if user_id == OWNER_ID and role is None:
            self.bot.db.add_bot_user(user_id, query.from_user.username, 'owner', user_id)
            role = 'owner'
        
        # Якщо користувача немає в системі
        if role is None:
            await query.edit_message_text(
                "❌ У вас немає доступу до бота.\n\nЗверніться до адміністратора.",
                parse_mode='Markdown'
            )
            return
        
        # Меню для власника/адмінів
        if role in ['owner', 'superadmin', 'admin']:
            keyboard = [
                [InlineKeyboardButton("👥 База користувачів", callback_data='users_base')],
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("👤 Користувачі бота", callback_data='bot_users_menu')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]
        # Меню для ментора
        elif role == 'mentor':
            keyboard = [
                [InlineKeyboardButton("🎥 Мої стрімери", callback_data='my_streamers')],
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]

        # show_start_menu_with_role — reply до update.message
        elif role == 'mentor':
            keyboard = [
                [InlineKeyboardButton("🎥 Мої стрімери", callback_data='my_streamers')],
                [InlineKeyboardButton("💝 Мої дарувальники", callback_data='my_donors_menu')],
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]

        # show_main_menu — edit_message_text
        elif role == 'mentor':
            keyboard = [
                [InlineKeyboardButton("🎥 Мої стрімери", callback_data='my_streamers')],
                [InlineKeyboardButton("💝 Мої дарувальники", callback_data='my_donors_menu')],
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]

        # Меню для гостя
        else:
            keyboard = [
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🤖 **Tango Bot**\n\nОберіть дію з меню:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_users_base_menu(self, query):
        """Меню бази користувачів"""
        keyboard = [
            [InlineKeyboardButton("🎥 Стрімери", callback_data='streamers_menu')],
            [InlineKeyboardButton("🎁 Дарувальники", callback_data='gifters_menu')],
            [InlineKeyboardButton("🎓 Ментори", callback_data='mentors_menu')],
            [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗂 База користувачів\n\nОберіть категорію:",
            reply_markup=reply_markup
        )

    async def show_start_menu_with_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE, role: str):
        """Показати головне меню з урахуванням ролі"""
        from config import OWNER_ID
        
        # Меню для власника/адмінів
        if role in ['owner', 'superadmin', 'admin']:
            keyboard = [
                [InlineKeyboardButton("👥 База користувачів", callback_data='users_base')],
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("👤 Користувачі бота", callback_data='bot_users_menu')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]
        # Меню для ментора
        elif role == 'mentor':
            keyboard = [
                [InlineKeyboardButton("🎥 Мої стрімери", callback_data='my_streamers')],
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]
        # Меню для гостя
        else:
            keyboard = [
                [InlineKeyboardButton("🆔 Отримати ID", callback_data='get_streamer_id')],
                [InlineKeyboardButton("❓ Допомога", callback_data='help')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome_text = "🤖 **Tango Bot**\n\nОберіть дію з меню:"
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_streamers_menu(self, query):
        """Меню стрімерів"""
        streamers_count = len(self.bot.db.get_all_streamers())
        keyboard = [
            [InlineKeyboardButton("➕ Додати стрімера", callback_data='add_streamer')],
            [InlineKeyboardButton("📋 Показати всіх", callback_data='show_streamers')],
            [InlineKeyboardButton("🔎 Пошук", callback_data='search_streamer')],
            [InlineKeyboardButton("🔍 Фільтрувати", callback_data='filter_streamers')],
            [InlineKeyboardButton("💎 Діамантів зараз", callback_data='update_diamonds_now')],
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
