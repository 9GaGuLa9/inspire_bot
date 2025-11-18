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
        keyboard = [
            [InlineKeyboardButton("👥 База користувачів", callback_data='users_base')],
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
    
    async def show_streamers_menu(self, query):
        """Меню стрімерів"""
        streamers_count = len(self.bot.db.get_all_streamers())
        keyboard = [
            [InlineKeyboardButton("➕ Додати стрімера", callback_data='add_streamer')],
            [InlineKeyboardButton("➖ Видалити стрімера", callback_data='remove_streamer')],
            [InlineKeyboardButton("📋 Показати всіх", callback_data='show_streamers')],
            [InlineKeyboardButton("🔎 Пошук по імені", callback_data='search_streamer')],
            [InlineKeyboardButton("🔍 Фільтрувати", callback_data='filter_streamers')],
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
