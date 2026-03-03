"""
Основний клас Tango Bot
"""
import logging
from typing import Dict
from telegram import Update
from telegram.ext import ContextTypes

from database_manager import DatabaseManager
from services.tango_api_client import TangoAPIClient
from services.gifter_search import GifterSearcher
from handlers.menu_handlers import MenuHandlers
from handlers.streamer_handlers import StreamerHandlers
from handlers.gifter_handlers import GifterHandlers
from handlers.search_handlers import SearchHandlers
from handlers.mentor_handlers import MentorHandlers
from handlers.callback_router import CallbackRouter
from handlers.bot_users_handlers import BotUsersHandlers
from services.diamonds_service import DiamondsService
from services.google_sheets_service import GoogleSheetsService
from services.scheduler import TaskScheduler
from handlers.diamonds_handlers import DiamondsHandlers


class TangoBot:
    """Основний клас Telegram бота для роботи з Tango"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = None  # Буде встановлено в main.py
        self.db = DatabaseManager()
        self.diamonds_service = DiamondsService(db=self.db, bot=self)
        self.sheets_service = GoogleSheetsService(db=self.db, bot=self)
        self.scheduler = TaskScheduler(bot=self)
        self.api_client = TangoAPIClient()  # API клієнт
        self.gifter_searcher = GifterSearcher()  # Пошук дарувальників
        self.user_states: Dict[int, str] = {}
        self.temp_data: Dict[int, Dict] = {}
        
        # Ініціалізуємо handler'и
        self.menu_handlers = MenuHandlers(self)
        self.streamer_handlers = StreamerHandlers(self)
        self.gifter_handlers = GifterHandlers(self)
        self.search_handlers = SearchHandlers(self)
        self.mentor_handlers = MentorHandlers(self)
        self.callback_router = CallbackRouter(self)
        self.bot_users_handlers = BotUsersHandlers(self)
        self.diamonds_handlers = DiamondsHandlers(bot=self)

        logging.info("TangoBot initialized successfully")
    
    async def on_startup(application) -> None:
        """Викликається після ініціалізації бота"""
        bot = application.bot_data.get('bot_instance')
        if bot is None:
            return

        # Запуск фонових сервісів
        await bot.sheets_service.start_background_worker()
        await bot.scheduler.start()

        # Перевірка пропущеного місячного оновлення
        await bot.diamonds_service.check_missed_monthly_update()

        # Початкова синхронізація з Sheets (у фоні)
        bot.sheets_service.schedule_all()

        logging.info("Bot startup complete")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start - показати головне меню або обробити активацію"""
        from config import OWNER_ID
        
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        
        # Перевіряємо чи є параметри (активація)
        if context.args and len(context.args) > 0:
            param = context.args[0]
            
            # Активація користувача через код
            if param.startswith('activate_'):
                activation_code = param.replace('activate_', '')
                await self.bot_users_handlers.handle_user_activation(update, activation_code)
                return
            
            # Активація ментора (стара система)
            if param.startswith('mentor_'):
                activation_code = param.replace('mentor_', '')
                await self.mentor_handlers.handle_mentor_activation(update, activation_code)
                return
        
        # Звичайний старт - перевірка доступу
        role = self.db.get_user_role(user_id)
        
        # Якщо користувач - власник, але немає в БД
        if user_id == OWNER_ID and role is None:
            self.db.add_bot_user(user_id, username, 'owner', user_id)
            role = 'owner'
        
        # Якщо користувача немає в системі
        if role is None:
            await update.message.reply_text(
                "❌ У вас немає доступу до бота.\n\nЗверніться до адміністратора.",
                parse_mode='Markdown'
            )
            return
        
        # Показуємо меню залежно від ролі
        await self.menu_handlers.show_start_menu_with_role(update, context, role)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Головний роутер для обробки callback кнопок"""
        await self.callback_router.route_callback(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка текстових повідомлень"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id in self.user_states:
            state = self.user_states[user_id]
            
            # Роутинг по станам
            if state == 'waiting_streamer_url':
                await self.streamer_handlers.process_streamer_url(update, text, user_id)
            elif state == 'waiting_gifter_url':
                await self.gifter_handlers.process_gifter_url(update, text, user_id)
            elif state == 'waiting_telegram_url':
                await self.streamer_handlers.process_telegram_url(update, text, user_id)
            elif state == 'waiting_instagram_url':
                await self.streamer_handlers.process_instagram_url(update, text, user_id)
            elif state == 'waiting_search_query':
                await self.streamer_handlers.process_search_query(update, text, user_id)
            elif state == 'waiting_get_id_url':
                await self.streamer_handlers.process_get_id_url(update, text, user_id)
            elif state == 'waiting_edit_name':
                await self.streamer_handlers.process_edit_name(update, text, user_id)
            elif state == 'waiting_edit_telegram':
                await self.streamer_handlers.process_edit_telegram(update, text, user_id)
            elif state == 'waiting_edit_instagram':
                await self.streamer_handlers.process_edit_instagram(update, text, user_id)
            elif state == 'waiting_new_user_username':
                await self.bot_users_handlers.process_new_user_username(update, text, user_id)
            elif state == 'waiting_new_user_id':
                await self.bot_users_handlers.process_new_user_id(update, text, user_id)

            # Ментори - додавання
            elif state == 'waiting_mentor_name':
                await self.mentor_handlers.process_mentor_name(update, text, user_id)
            elif state == 'waiting_mentor_url':
                await self.mentor_handlers.process_mentor_url(update, text, user_id)
            elif state == 'waiting_mentor_telegram':
                await self.mentor_handlers.process_mentor_telegram(update, text, user_id)
            elif state == 'waiting_mentor_instagram':
                await self.mentor_handlers.process_mentor_instagram(update, text, user_id)
            
            # Ментори - редагування
            elif state == 'waiting_edit_mentor_url':
                await self.mentor_handlers.process_edit_mentor_url(update, text, user_id)
            elif state == 'waiting_edit_mentor_telegram':
                await self.mentor_handlers.process_edit_mentor_telegram(update, text, user_id)
            elif state == 'waiting_edit_mentor_instagram':
                await self.mentor_handlers.process_edit_mentor_instagram(update, text, user_id)
            
            else:
                await update.message.reply_text("❌ Невідомий стан. Використовуйте /start")
        else:
            await update.message.reply_text(
                "👋 Використовуйте /start для відображення меню"
            )