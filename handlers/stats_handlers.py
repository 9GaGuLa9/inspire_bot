# stats_handlers.py
# Обробники для статистики

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from role_decorators import *
import config

logger = logging.getLogger(__name__)


class StatsHandlers:
    """Клас для обробки статистики"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ================================
    # ГОЛОВНЕ МЕНЮ СТАТИСТИКИ
    # ================================
    
    @mentor_or_higher
    async def show_stats_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             user_role=None, user_data=None):
        """Показує меню статистики"""
        query = update.callback_query
        if query:
            await query.answer()
        
        keyboard = []
        
        # Ментор бачить тільки свою статистику
        if user_role == 'mentor':
            keyboard.extend([
                [InlineKeyboardButton("📊 Моя статистика", callback_data='stats_my')],
            ])
        
        # Адмін і вище бачать загальну статистику
        if user_role in ['admin', 'superadmin', 'owner']:
            keyboard.extend([
                [InlineKeyboardButton("📊 Загальна статистика", callback_data='stats_general')],
                [InlineKeyboardButton("🎯 Статистика менторів", callback_data='stats_mentors')],
                [InlineKeyboardButton("👥 Статистика користувачів", callback_data='stats_users')],
            ])
        
        # Власник має додаткові опції
        if user_role == 'owner':
            keyboard.append([InlineKeyboardButton("📁 Експорт даних", callback_data='stats_export')])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='main_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "📊 <b>Статистика</b>\n\nОберіть тип статистики:"
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # МОЯ СТАТИСТИКА (ДЛЯ МЕНТОРА)
    # ================================
    
    @mentor_or_higher
    async def show_my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                           user_role=None, user_data=None):
        """Показує особисту статистику ментора"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Отримуємо ID ментора з таблиці mentors
        mentor = self.bot.db.get_mentor_by_telegram_id(user_id)
        
        if not mentor:
            text = "📊 <b>Моя статистика</b>\n\n❌ Ви не зареєстровані як ментор"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]]
        else:
            # Отримуємо стрімерів ментора
            streamers = self.bot.db.get_streamers_by_mentor(mentor['id'])
            active_streamers = [s for s in streamers if s.get('is_active')]
            inactive_streamers = [s for s in streamers if not s.get('is_active')]
            
            # Отримуємо даруваників стрімерів
            total_donors = 0
            for streamer in streamers:
                donors = self.bot.db.get_donors_by_streamer(streamer['id'])
                total_donors += len(donors)
            
            # Особисті даруваники
            personal_donors = self.bot.db.get_user_donors(user_id)
            
            text = (
                f"📊 <b>Моя статистика</b>\n\n"
                f"👤 Ментор: {mentor['name']}\n\n"
                f"<b>Стрімери:</b>\n"
                f"• Всього: {len(streamers)}\n"
                f"• Активних: {len(active_streamers)}\n"
                f"• Неактивних: {len(inactive_streamers)}\n\n"
                f"<b>Даруваники стрімерів:</b>\n"
                f"• Всього: {total_donors}\n\n"
                f"<b>Особисті даруваники:</b>\n"
                f"• Всього: {len(personal_donors)}\n"
            )
            
            keyboard = [
                [InlineKeyboardButton("🎯 Мої стрімери", callback_data='filter_my_streamers')],
                [InlineKeyboardButton("💝 Мої даруваники", callback_data='my_donors_menu')],
                [InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ЗАГАЛЬНА СТАТИСТИКА (ДЛЯ АДМІНА+)
    # ================================
    
    @admin_or_higher
    async def show_general_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_role=None, user_data=None):
        """Показує загальну статистику"""
        query = update.callback_query
        await query.answer()
        
        stats = self.bot.db.get_statistics()
        
        text = (
            f"📊 <b>Загальна статистика системи</b>\n\n"
            f"<b>Користувачі:</b>\n"
        )
        
        # Користувачі по ролях
        for role, count in sorted(stats.get('users_by_role', {}).items(), 
                                  key=lambda x: config.ROLE_HIERARCHY.get(x[0], 0), 
                                  reverse=True):
            role_emoji = config.ROLE_EMOJI.get(role, '👤')
            role_name = config.ROLES.get(role, role)
            text += f"{role_emoji} {role_name}: {count}\n"
        
        text += (
            f"\n<b>Стрімери:</b>\n"
            f"• Всього: {stats.get('total_streamers', 0)}\n"
            f"• Активних: {stats.get('active_streamers', 0)}\n"
            f"• Неактивних: {stats.get('total_streamers', 0) - stats.get('active_streamers', 0)}\n"
            f"• Без ментора: {stats.get('streamers_no_mentor', 0)}\n"
            f"• З видаленим ментором: {stats.get('streamers_deleted_mentor', 0)}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎯 Детально по менторах", callback_data='stats_mentors')],
            [InlineKeyboardButton("👥 Детально по користувачах", callback_data='stats_users')],
            [InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # СТАТИСТИКА МЕНТОРІВ (ДЛЯ АДМІНА+)
    # ================================
    
    @admin_or_higher
    async def show_mentors_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_role=None, user_data=None):
        """Показує статистику по менторах"""
        query = update.callback_query
        await query.answer()
        
        stats = self.bot.db.get_statistics()
        streamers_by_mentor = stats.get('streamers_by_mentor', {})
        
        if not streamers_by_mentor:
            text = "🎯 <b>Статистика менторів</b>\n\n📭 Менторів без стрімерів"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]]
        else:
            # Сортуємо менторів по кількості стрімерів
            sorted_mentors = sorted(streamers_by_mentor.items(), 
                                   key=lambda x: x[1], 
                                   reverse=True)
            
            text = f"🎯 <b>Статистика менторів</b>\n\n📊 Всього менторів: {len(sorted_mentors)}\n\n"
            
            for mentor_name, count in sorted_mentors:
                # Отримуємо детальну інформацію про ментора
                mentor = self.bot.db.get_mentor_by_name(mentor_name)
                if mentor:
                    streamers = self.bot.db.get_streamers_by_mentor(mentor['id'])
                    active = len([s for s in streamers if s.get('is_active')])
                    text += f"👤 {mentor_name}\n   📊 Всього: {count} | Активних: {active}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # СТАТИСТИКА КОРИСТУВАЧІВ (ДЛЯ АДМІНА+)
    # ================================
    
    @admin_or_higher
    async def show_users_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              user_role=None, user_data=None):
        """Показує статистику по користувачах"""
        query = update.callback_query
        await query.answer()
        
        all_users = self.bot.db.get_all_users()
        
        # Групуємо по ролях
        by_role = {}
        for user in all_users:
            role = user['role']
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(user)
        
        text = f"👥 <b>Статистика користувачів</b>\n\n📊 Всього: {len(all_users)}\n\n"
        
        # По кожній ролі
        for role in ['owner', 'superadmin', 'admin', 'mentor', 'guest']:
            if role in by_role:
                role_emoji = config.ROLE_EMOJI.get(role, '👤')
                role_name = config.ROLES.get(role, role)
                count = len(by_role[role])
                text += f"{role_emoji} {role_name}: {count}\n"
        
        # Додаткова інформація про менторів
        if 'mentor' in by_role:
            text += f"\n<b>Деталі по менторах:</b>\n"
            for user in by_role['mentor'][:10]:  # Показуємо топ-10
                mentor = self.bot.db.get_mentor_by_telegram_id(user['telegram_id'])
                if mentor:
                    streamers = self.bot.db.get_streamers_by_mentor(mentor['id'])
                    text += f"• {user.get('full_name', 'N/A')}: {len(streamers)} стрімерів\n"
        
        keyboard = [
            [InlineKeyboardButton("👥 Управління користувачами", callback_data='users_menu')],
            [InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # ================================
    # ЕКСПОРТ ДАНИХ (ДЛЯ ВЛАСНИКА)
    # ================================
    
    @owner_only
    async def show_export_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                              user_role=None, user_data=None):
        """Показує меню експорту даних"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📊 Експорт стрімерів (CSV)", callback_data='export_streamers_csv')],
            [InlineKeyboardButton("📊 Експорт стрімерів (Excel)", callback_data='export_streamers_excel')],
            [InlineKeyboardButton("👥 Експорт користувачів (CSV)", callback_data='export_users_csv')],
            [InlineKeyboardButton("📋 Експорт аудит-логу (CSV)", callback_data='export_audit_csv')],
            [InlineKeyboardButton("💝 Експорт даруваників (CSV)", callback_data='export_donors_csv')],
            [InlineKeyboardButton("◀️ Назад", callback_data='stats_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "📁 <b>Експорт даних</b>\n\n"
            "Оберіть що експортувати:"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    @owner_only
    async def export_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                         data_type: str, format_type: str, 
                         user_role=None, user_data=None):
        """Експортує дані в CSV або Excel"""
        query = update.callback_query
        await query.answer("⏳ Готую експорт...", show_alert=False)
        
        try:
            if data_type == 'streamers':
                filename = await self._export_streamers(format_type)
            elif data_type == 'users':
                filename = await self._export_users(format_type)
            elif data_type == 'audit':
                filename = await self._export_audit(format_type)
            elif data_type == 'donors':
                filename = await self._export_donors(format_type)
            else:
                await query.answer("❌ Невідомий тип даних", show_alert=True)
                return
            
            # Надсилаємо файл
            with open(filename, 'rb') as file:
                await query.message.reply_document(
                    document=file,
                    caption=f"✅ Експорт готовий: {data_type}"
                )
            
            await query.answer("✅ Файл надіслано!", show_alert=False)
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            await query.answer("❌ Помилка при експорті", show_alert=True)
    
    # ================================
    # ДОПОМІЖНІ МЕТОДИ ЕКСПОРТУ
    # ================================
    
    async def _export_streamers(self, format_type: str) -> str:
        """Експортує стрімерів"""
        import csv
        from datetime import datetime
        
        filename = f"streamers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Отримуємо всіх стрімерів (тут має бути метод в database.py)
        streamers = []  # self.bot.db.get_all_streamers()
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['ID', 'Ім\'я', 'Telegram', 'Instagram', 'Платформа', 'Ментор', 'Активний', 'Дата створення']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for s in streamers:
                writer.writerow({
                    'ID': s['user_id'],
                    'Ім\'я': s['name'],
                    'Telegram': s.get('telegram', ''),
                    'Instagram': s.get('instagram', ''),
                    'Платформа': s.get('platform', ''),
                    'Ментор': s.get('mentor_name', ''),
                    'Активний': 'Так' if s.get('is_active') else 'Ні',
                    'Дата створення': s['created_at'][:10]
                })
        
        return filename
    
    async def _export_users(self, format_type: str) -> str:
        """Експортує користувачів"""
        import csv
        from datetime import datetime
        
        filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        users = self.bot.db.get_all_users()
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Telegram ID', 'Username', 'ПІБ', 'Роль', 'Дата створення']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for u in users:
                writer.writerow({
                    'Telegram ID': u['telegram_id'],
                    'Username': u.get('username', ''),
                    'ПІБ': u.get('full_name', ''),
                    'Роль': config.ROLES.get(u['role'], u['role']),
                    'Дата створення': u['created_at'][:10]
                })
        
        return filename
    
    async def _export_audit(self, format_type: str) -> str:
        """Експортує аудит-лог"""
        import csv
        from datetime import datetime
        
        filename = f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        logs = self.bot.db.get_audit_logs(limit=10000)
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Дата', 'Користувач', 'Дія', 'Об\'єкт', 'Ціль']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    'Дата': log['created_at'],
                    'Користувач': log['user_name'],
                    'Дія': log['action_type'],
                    'Об\'єкт': log['target_type'],
                    'Ціль': log['target_name']
                })
        
        return filename
    
    async def _export_donors(self, format_type: str) -> str:
        """Експортує даруваників"""
        import csv
        from datetime import datetime
        
        filename = f"donors_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Експортуємо і стрімерських і особистих даруваників
        # Тут потрібні методи в database.py
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Тип', 'Власник', 'Ім\'я даруваника', 'Tango ID', 'Дата']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # TODO: Додати експорт даруваників
        
        return filename
