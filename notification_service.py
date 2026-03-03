# notification_service.py
# Сервіс для відправки сповіщень користувачам та в канал

import logging
from telegram import Bot
from telegram.error import TelegramError
from typing import List, Dict, Optional
from config import NOTIFICATION_CHANNEL_ID, ROLES, ROLE_EMOJI

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервіс для відправки сповіщень"""
    
    def __init__(self, bot: Bot, db):
        self.bot = bot
        self.db = db
    
    async def notify_new_streamer(self, streamer_data: Dict, added_by_name: str, 
                                 mentor_name: Optional[str] = None):
        """
        Сповіщення про новий стрімер в канал
        streamer_data: {name, user_id, profile_url, platform, mentor_name}
        added_by_name: ім'я того хто додав (може бути ментор або адмін)
        mentor_name: ім'я призначеного ментора (якщо адмін призначив іншого)
        """
        if not NOTIFICATION_CHANNEL_ID:
            return
        
        # Хто додав
        added_by_text = f"👤 Додав: {added_by_name}"
        
        # Ментор
        if mentor_name:
            mentor_text = f"🎓 Ментор: {mentor_name}"
            if mentor_name != added_by_name:
                # Адмін додав і призначив ментора
                mentor_text += f" (призначено {added_by_name})"
        else:
            mentor_text = "🎓 Ментор: не призначено"
        
        message = (
            f"✅ <b>Новий стрімер зареєстрований</b>\n\n"
            f"📛 Ім'я: {streamer_data['name']}\n"
            f"🆔 ID: <code>{streamer_data['user_id']}</code>\n"
            f"🔗 Профіль: <a href=\"{streamer_data['profile_url']}\">переглянути</a>\n"
        )
        
        if streamer_data.get('platform'):
            message += f"📱 Платформа: {streamer_data['platform']}\n"
        
        message += f"\n{mentor_text}\n{added_by_text}"
        
        await self._send_to_channel(message)
    
    async def notify_streamer_deleted(self, streamer_data: Dict, deleted_by_name: str,
                                     mentor_name: Optional[str] = None):
        """
        Сповіщення про видалення стрімера
        """
        if not NOTIFICATION_CHANNEL_ID:
            return
        
        message = (
            f"❌ <b>Стрімер видалений</b>\n\n"
            f"📛 Ім'я: {streamer_data['name']}\n"
            f"🆔 ID: <code>{streamer_data['user_id']}</code>\n"
            f"🔗 Профіль: <a href=\"{streamer_data['profile_url']}\">переглянути</a>\n"
        )
        
        if mentor_name:
            message += f"🎓 Ментор: {mentor_name}\n"
        
        message += f"👤 Видалив: {deleted_by_name}"
        
        await self._send_to_channel(message)
    
    async def notify_mentor_reassignment(self, streamer_data: Dict, old_mentor_name: str,
                                        new_mentor_name: str, changed_by_name: str):
        """
        Сповіщення про перепризначення ментора
        """
        if not NOTIFICATION_CHANNEL_ID:
            return
        
        message = (
            f"🔄 <b>Ментор змінено</b>\n\n"
            f"📛 Стрімер: {streamer_data['name']}\n"
            f"🆔 ID: <code>{streamer_data['user_id']}</code>\n"
            f"🔗 Профіль: <a href=\"{streamer_data['profile_url']}\">переглянути</a>\n\n"
            f"Було: {old_mentor_name}\n"
            f"Стало: {new_mentor_name}\n\n"
            f"👤 Змінив: {changed_by_name}"
        )
        
        await self._send_to_channel(message)
    
    async def notify_user_role_assigned(self, telegram_id: int, role: str, 
                                       first_name: Optional[str] = None):
        """
        Сповіщає користувача про призначену роль
        """
        role_emoji = ROLE_EMOJI.get(role, '👤')
        role_name = ROLES.get(role, role)
        
        greeting = f"Вітаємо, {first_name}!" if first_name else "Вітаємо!"
        
        message = (
            f"{role_emoji} <b>{greeting}</b>\n\n"
            f"Вас додано до бота з роллю: <b>{role_name}</b>\n\n"
        )
        
        # Додаємо опис можливостей залежно від ролі
        if role == 'mentor':
            message += (
                "📋 <b>Ваші можливості:</b>\n"
                "• Додавання та редагування своїх стрімерів\n"
                "• Видалення своїх стрімерів\n"
                "• Додавання дарувальників\n"
                "• Перегляд статистики\n"
                "• Фільтрування та пошук\n"
                "• Отримання ID з посилань Tango\n"
            )
        elif role == 'admin':
            message += (
                "📋 <b>Ваші можливості:</b>\n"
                "• Додавання Менторів та Гостей\n"
                "• Управління всіма стрімерами\n"
                "• Переприв'язування стрімерів між менторами\n"
                "• Управління дарувальниками\n"
                "• Перегляд повної статистики\n"
            )
        elif role == 'superadmin':
            message += (
                "📋 <b>Ваші можливості:</b>\n"
                "• Додавання Адмінів, Менторів та Гостей\n"
                "• Повне управління всіма користувачами\n"
                "• Управління всіма стрімерами\n"
                "• Переприв'язування стрімерів\n"
                "• Повний доступ до всіх функцій\n"
            )
        elif role == 'guest':
            message += (
                "📋 <b>Ваші можливості:</b>\n"
                "• Отримати ID стрімера з посилання Tango\n"
            )
        
        message += "\n\nДля початку роботи натисніть /start"
        
        await self._send_message(telegram_id, message)
    
    async def notify_user_role_changed(self, telegram_id: int, old_role: str, 
                                      new_role: str, changed_by: str):
        """
        Сповіщає користувача про зміну ролі
        """
        old_role_name = ROLES.get(old_role, old_role)
        new_role_name = ROLES.get(new_role, new_role)
        new_role_emoji = ROLE_EMOJI.get(new_role, '👤')
        
        message = (
            f"{new_role_emoji} <b>Вашу роль змінено!</b>\n\n"
            f"Попередня роль: {old_role_name}\n"
            f"Нова роль: <b>{new_role_name}</b>\n"
            f"Хто змінив: {changed_by}\n"
        )
        
        await self._send_message(telegram_id, message)
    
    async def _send_to_channel(self, message: str):
        """Відправляє повідомлення в канал сповіщень"""
        if not NOTIFICATION_CHANNEL_ID:
            logger.warning("NOTIFICATION_CHANNEL_ID not configured")
            return
        
        try:
            await self.bot.send_message(
                chat_id=NOTIFICATION_CHANNEL_ID,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"Notification sent to channel {NOTIFICATION_CHANNEL_ID}")
        except TelegramError as e:
            logger.error(f"Failed to send notification to channel: {e}")
    
    async def _send_message(self, telegram_id: int, message: str):
        """Відправляє повідомлення одному користувачу"""
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"Notification sent to {telegram_id}")
        except TelegramError as e:
            logger.error(f"Failed to send notification to {telegram_id}: {e}")
