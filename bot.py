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
from handlers.callback_router import CallbackRouter


class TangoBot:
    """Основний клас Telegram бота для роботи з Tango"""
    
    def __init__(self, token: str):
        self.token = token
        self.db = DatabaseManager()
        self.api_client = TangoAPIClient()  # API клієнт
        self.gifter_searcher = GifterSearcher()  # Пошук дарувальників
        self.user_states: Dict[int, str] = {}
        self.temp_data: Dict[int, Dict] = {}
        
        # Ініціалізуємо handler'и
        self.menu_handlers = MenuHandlers(self)
        self.streamer_handlers = StreamerHandlers(self)
        self.gifter_handlers = GifterHandlers(self)
        self.search_handlers = SearchHandlers(self)
        self.callback_router = CallbackRouter(self)
        
        logging.info("TangoBot initialized successfully")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start - показати головне меню"""
        await self.menu_handlers.show_start_menu(update, context)
    
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
            elif state == 'waiting_edit_name':
                await self.streamer_handlers.process_edit_name(update, text, user_id)
            elif state == 'waiting_edit_telegram':
                await self.streamer_handlers.process_edit_telegram(update, text, user_id)
            elif state == 'waiting_edit_instagram':
                await self.streamer_handlers.process_edit_instagram(update, text, user_id)
        else:
            # Видаляємо невідомі повідомлення
            try:
                await update.message.delete()
            except:
                pass
