# audit_handlers.py
# Обробники для перегляду аудит-логу

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from role_decorators import *
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class AuditHandlers:
    """Клас для обробки операцій з аудит-логом"""
    
    def __init__(self, bot):
        self.bot = bot
    
    ACTION_TYPES = {
        'add_streamer': '➕ Додавання стрімера',
        'edit_streamer': '✏️ Редагування стрімера',
        'delete_streamer': '🗑 Видалення стрімера',
        'assign_mentor': '🎯 Призначення ментора',
        'reassign_mentor': '🔄 Переприв'язування ментора',
        'add_donor': '➕ Додавання даруваника',
        'delete_donor': '🗑 Видалення даруваника',
        'add_user': '➕ Додавання користувача',
        'edit_user': '✏️ Редагування користувача',
        'delete_user': '🗑 Видалення користувача',
        'role_change': '🔄 Зміна ролі',
    }
    
    # ================================
    # ГОЛОВНЕ МЕНЮ АУДИТ-ЛОГУ
    # ================================
    
    @admin_or_higher
    async def show_audit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             user_role=None, user_data=None):
        """Показує меню аудит-логу"""
        query = update.callback_query
        if query:
            await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📋 Останні 50 дій", callback_data='audit_recent_50')],
            [InlineKeyboardButton("📋 Останні 100 дій", callback_data='audit_recent_100')],
            [InlineKeyboardButton("📅 За сьогодні", callback_data='audit_today')],
            [InlineKeyboardButton("📅 За тиждень", callback_data='audit_week')],
            [InlineKeyboardButton("📅 За місяць", callback_data='audit_month')],
            [InlineKeyboardButton("🔍 Фільтри", callback_data='audit_filters')],
            [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "📋 <b>Аудит-лог</b>\n\nОберіть період або налаштуйте фільтри:"
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ПЕРЕГЛЯД ЛОГІВ
    # ================================
    
    @admin_or_higher
    async def show_recent_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              limit: int, user_role=None, user_data=None):
        """Показує останні записи логу"""
        query = update.callback_query
        await query.answer()
        
        logs = self.bot.db.get_audit_logs(limit=limit)
        
        if not logs:
            text = "📋 <b>Аудит-лог</b>\n\n📭 Записів немає"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='audit_menu')]]
        else:
            text = f"📋 <b>Останні {len(logs)} дій</b>\n\n"
            
            for log in logs[:20]:  # Показуємо тільки перші 20 в повідомленні
                action_name = self.ACTION_TYPES.get(log['action_type'], log['action_type'])
                date_time = log['created_at'][:16]  # YYYY-MM-DD HH:MM
                
                text += (
                    f"{action_name}\n"
                    f"👤 {log['user_name']}\n"
                    f"🎯 {log['target_name']}\n"
                    f"🕐 {date_time}\n\n"
                )
            
            if len(logs) > 20:
                text += f"... та ще {len(logs) - 20} записів"
            
            keyboard = [
                [InlineKeyboardButton("📊 Експорт", callback_data=f'audit_export_{limit}')],
                [InlineKeyboardButton("◀️ Назад", callback_data='audit_menu')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def show_logs_by_period(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 period: str, user_role=None, user_data=None):
        """Показує логи за період"""
        query = update.callback_query
        await query.answer()
        
        now = datetime.now()
        
        if period == 'today':
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "сьогодні"
        elif period == 'week':
            date_from = now - timedelta(days=7)
            period_name = "за тиждень"
        elif period == 'month':
            date_from = now - timedelta(days=30)
            period_name = "за місяць"
        else:
            return
        
        date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S')
        logs = self.bot.db.get_audit_logs(limit=1000, date_from=date_from_str)
        
        if not logs:
            text = f"📋 <b>Аудит-лог {period_name}</b>\n\n📭 Записів немає"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='audit_menu')]]
        else:
            # Підрахунок статистики
            stats = self._calculate_stats(logs)
            
            text = (
                f"📋 <b>Аудит-лог {period_name}</b>\n\n"
                f"📊 Всього дій: {len(logs)}\n\n"
                f"<b>За типами:</b>\n"
            )
            
            for action_type, count in sorted(stats['by_action'].items(), key=lambda x: x[1], reverse=True):
                action_name = self.ACTION_TYPES.get(action_type, action_type)
                text += f"{action_name}: {count}\n"
            
            text += f"\n<b>Останні 15 дій:</b>\n\n"
            
            for log in logs[:15]:
                action_name = self.ACTION_TYPES.get(log['action_type'], log['action_type'])
                date_time = log['created_at'][5:16]  # MM-DD HH:MM
                text += f"{action_name} - {log['user_name']} - {date_time}\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 Детальніше", callback_data=f'audit_detailed_{period}')],
                [InlineKeyboardButton("◀️ Назад", callback_data='audit_menu')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ФІЛЬТРИ
    # ================================
    
    @admin_or_higher
    async def show_filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               user_role=None, user_data=None):
        """Показує меню фільтрів"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("👤 По користувачу", callback_data='audit_filter_user')],
            [InlineKeyboardButton("📝 По типу дії", callback_data='audit_filter_action')],
            [InlineKeyboardButton("🎯 По цільовому об'єкту", callback_data='audit_filter_target')],
            [InlineKeyboardButton("◀️ Назад", callback_data='audit_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "🔍 <b>Фільтри аудит-логу</b>\n\nОберіть фільтр:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def show_action_type_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     user_role=None, user_data=None):
        """Показує фільтр по типу дії"""
        query = update.callback_query
        await query.answer()
        
        keyboard = []
        
        for action_type, action_name in self.ACTION_TYPES.items():
            keyboard.append([
                InlineKeyboardButton(
                    action_name,
                    callback_data=f'audit_show_action_{action_type}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='audit_filters')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "📝 <b>Фільтр по типу дії</b>\n\nОберіть тип:"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @admin_or_higher
    async def show_logs_by_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 action_type: str, user_role=None, user_data=None):
        """Показує логи по типу дії"""
        query = update.callback_query
        await query.answer()
        
        logs = self.bot.db.get_audit_logs(limit=100, action_type=action_type)
        
        action_name = self.ACTION_TYPES.get(action_type, action_type)
        
        if not logs:
            text = f"📝 <b>{action_name}</b>\n\n📭 Записів немає"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='audit_filter_action')]]
        else:
            text = f"📝 <b>{action_name}</b>\n\n📊 Всього: {len(logs)}\n\n"
            
            for log in logs[:15]:
                date_time = log['created_at'][5:16]
                text += f"👤 {log['user_name']}\n🎯 {log['target_name']}\n🕐 {date_time}\n\n"
            
            if len(logs) > 15:
                text += f"... та ще {len(logs) - 15} записів"
            
            keyboard = [
                [InlineKeyboardButton("📊 Детальніше", callback_data=f'audit_action_details_{action_type}')],
                [InlineKeyboardButton("◀️ Назад", callback_data='audit_filter_action')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДЕТАЛЬНИЙ ПЕРЕГЛЯД
    # ================================
    
    @admin_or_higher
    async def show_log_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              log_id: int, user_role=None, user_data=None):
        """Показує детальну інформацію про запис логу"""
        query = update.callback_query
        await query.answer()
        
        logs = self.bot.db.get_audit_logs(limit=1000)
        log = next((l for l in logs if l['id'] == log_id), None)
        
        if not log:
            await query.answer("❌ Запис не знайдено", show_alert=True)
            return
        
        action_name = self.ACTION_TYPES.get(log['action_type'], log['action_type'])
        
        text = (
            f"📋 <b>Деталі запису аудит-логу</b>\n\n"
            f"📝 Дія: {action_name}\n"
            f"👤 Користувач: {log['user_name']}\n"
            f"🆔 User ID: <code>{log['user_telegram_id']}</code>\n"
            f"🎯 Об'єкт: {log['target_type']}\n"
            f"📛 Назва: {log['target_name']}\n"
            f"🔢 Target ID: <code>{log['target_id']}</code>\n"
            f"🕐 Дата: {log['created_at']}\n"
        )
        
        # Додаткові деталі
        if log.get('details'):
            try:
                details = json.loads(log['details'])
                if details:
                    text += "\n<b>Деталі:</b>\n"
                    for key, value in details.items():
                        text += f"• {key}: {value}\n"
            except:
                pass
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='audit_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ДОПОМІЖНІ МЕТОДИ
    # ================================
    
    def _calculate_stats(self, logs):
        """Розраховує статистику по логам"""
        stats = {
            'by_action': {},
            'by_user': {},
            'by_target': {}
        }
        
        for log in logs:
            # По діях
            action = log['action_type']
            stats['by_action'][action] = stats['by_action'].get(action, 0) + 1
            
            # По користувачах
            user = log['user_name']
            stats['by_user'][user] = stats['by_user'].get(user, 0) + 1
            
            # По цільових об'єктах
            target = log['target_type']
            stats['by_target'][target] = stats['by_target'].get(target, 0) + 1
        
        return stats
