"""
Роутер для обробки всіх callback запитів
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes


class CallbackRouter:
    """Маршрутизація callback запитів до відповідних handler'ів"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def route_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Головний роутер callback'ів"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Меню
        if data == 'main_menu':
            await self.bot.menu_handlers.show_main_menu(query)
        elif data == 'users_base':
            await self.bot.menu_handlers.show_users_base_menu(query)
        elif data == 'streamers_menu':
            await self.bot.menu_handlers.show_streamers_menu(query)
        elif data == 'gifters_menu':
            await self.bot.menu_handlers.show_gifters_menu(query)
        elif data == 'mentors_menu':
            await self.bot.mentor_handlers.show_mentors_menu(query)
        elif data == 'help':
            await self.bot.menu_handlers.show_help(query)
            
        # Стрімери
        elif data == 'add_streamer':
            await self.bot.streamer_handlers.start_add_streamer(query, user_id)
        elif data == 'remove_streamer':
            await self.bot.streamer_handlers.start_remove_streamer(query, user_id)
        elif data == 'show_streamers':
            await self.bot.streamer_handlers.show_all_streamers(query)
        elif data == 'search_streamer':
            await self.bot.streamer_handlers.start_search_streamer(query, user_id)
            
        # Фільтрація
        elif data == 'filter_streamers':
            await self.bot.streamer_handlers.show_filter_menu(query, user_id)
        elif data == 'filter_by_year':
            await self.bot.streamer_handlers.show_year_selection(query, user_id)
        elif data == 'filter_by_month':
            await self.bot.streamer_handlers.show_year_selection_for_month(query, user_id)
        elif data == 'show_statistics':
            await self.bot.streamer_handlers.show_statistics(query)
            
        # Роки та місяці
        elif data.startswith('year_for_month_'):
            year = int(data.replace('year_for_month_', ''))
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['selected_year'] = year
            await self.bot.streamer_handlers.show_month_selection(query, user_id, year)
        elif data.startswith('year_'):
            year = int(data.replace('year_', ''))
            await self.bot.streamer_handlers.show_streamers_by_year(query, year)
        elif data.startswith('month_'):
            await self._handle_month_selection(query, user_id, data)
        elif data.startswith('back_to_months_'):
            year = int(data.replace('back_to_months_', ''))
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['selected_year'] = year
            await self.bot.streamer_handlers.show_month_selection(query, user_id, year)
            
        # Видалення та підтвердження
        elif data.startswith('del_streamer_'):
            await self.bot.streamer_handlers.delete_streamer(query, data.replace('del_streamer_', ''))
        elif data.startswith('confirm_delete_'):
            await self.bot.streamer_handlers.confirm_delete_streamer(query, data.replace('confirm_delete_', ''))
        elif data.startswith('del_gifter_'):
            await self.bot.gifter_handlers.delete_gifter(query, data.replace('del_gifter_', ''))
            
        # Дарувальники
        elif data == 'add_gifter':
            await self.bot.gifter_handlers.start_add_gifter(query, user_id)
        elif data == 'show_gifters':
            await self.bot.gifter_handlers.show_all_gifters(query)
        elif data == 'search_gifters':
            await self.bot.search_handlers.start_search_gifters(query, user_id)
        elif data.startswith('select_gifter_'):
            await self.bot.search_handlers.toggle_gifter_selection(query, user_id, data.replace('select_gifter_', ''))
        elif data == 'start_search':
            await self.bot.search_handlers.execute_search(query, user_id)
            
        # Додаткові дані стрімера
        elif data == 'add_more_data':
            await self.bot.streamer_handlers.show_additional_data_menu(query, user_id)
        elif data == 'skip_additional_data' or data == 'finish_adding':
            await self.bot.streamer_handlers.finish_streamer_adding(query, user_id)
        elif data == 'add_telegram':
            await self.bot.streamer_handlers.start_add_telegram(query, user_id)
        elif data == 'add_instagram':
            await self.bot.streamer_handlers.start_add_instagram(query, user_id)
        elif data == 'add_platform':
            await self.bot.streamer_handlers.show_platform_selection(query, user_id)
        elif data == 'platform_ios':
            await self.bot.streamer_handlers.set_platform(query, user_id, 'iOS')
        elif data == 'platform_android':
            await self.bot.streamer_handlers.set_platform(query, user_id, 'Android')
            
        # Редагування стрімера
        elif data.startswith('edit_streamer_'):
            await self.bot.streamer_handlers.show_edit_streamer_menu(query, user_id, data.replace('edit_streamer_', ''))
        elif data.startswith('edit_name_'):
            await self.bot.streamer_handlers.start_edit_name(query, user_id, data.replace('edit_name_', ''))
        elif data.startswith('edit_telegram_'):
            await self.bot.streamer_handlers.start_edit_telegram(query, user_id, data.replace('edit_telegram_', ''))
        elif data.startswith('edit_instagram_'):
            await self.bot.streamer_handlers.start_edit_instagram(query, user_id, data.replace('edit_instagram_', ''))
        elif data.startswith('edit_platform_'):
            await self.bot.streamer_handlers.show_edit_platform_menu(query, user_id, data.replace('edit_platform_', ''))
        elif data.startswith('set_platform_'):
            parts = data.replace('set_platform_', '').rsplit('_', 1)
            if len(parts) == 2:
                streamer_id, platform = parts
                await self.bot.streamer_handlers.update_platform(query, user_id, streamer_id, platform)
        elif data.startswith('remove_telegram_'):
            await self.bot.streamer_handlers.remove_field(query, user_id, data.replace('remove_telegram_', ''), 'telegram')
        elif data.startswith('remove_instagram_'):
            await self.bot.streamer_handlers.remove_field(query, user_id, data.replace('remove_instagram_', ''), 'instagram')
        elif data.startswith('remove_platform_'):
            await self.bot.streamer_handlers.remove_field(query, user_id, data.replace('remove_platform_', ''), 'platform')
            
        # Пагінація
        elif data.startswith('page_streamers_'):
            page = int(data.replace('page_streamers_', ''))
            await self.bot.streamer_handlers.show_all_streamers_paginated(query, page)
        elif data.startswith('page_delete_'):
            page = int(data.replace('page_delete_', ''))
            await self.bot.streamer_handlers.show_delete_page(query, user_id, page)
        
        # Ментори
        elif data == 'add_mentor':
            await self.bot.mentor_handlers.start_add_mentor(query, user_id)
        elif data == 'show_mentors':
            await self.bot.mentor_handlers.show_all_mentors(query)
        elif data == 'show_mentor_statistics':
            await self.bot.mentor_handlers.show_mentor_statistics(query)
        elif data == 'remove_mentor':
            await self.bot.mentor_handlers.start_remove_mentor(query, user_id)
        elif data == 'edit_mentor_select':
            await self.bot.mentor_handlers.show_edit_mentor_list(query)
        elif data == 'restore_mentor_select':
            await self.bot.mentor_handlers.show_restore_mentor_list(query)
        # ВАЖЛИВО: Специфічні callback'и ПЕРЕД загальним edit_mentor_
        elif data.startswith('edit_mentor_name_'):
            mentor_id = int(data.replace('edit_mentor_name_', ''))
            await self.bot.mentor_handlers.start_edit_mentor_name(query, user_id, mentor_id)
        elif data.startswith('edit_mentor_telegram_'):
            mentor_id = int(data.replace('edit_mentor_telegram_', ''))
            await self.bot.mentor_handlers.start_edit_mentor_telegram(query, user_id, mentor_id)
        elif data.startswith('edit_mentor_instagram_'):
            mentor_id = int(data.replace('edit_mentor_instagram_', ''))
            await self.bot.mentor_handlers.start_edit_mentor_instagram(query, user_id, mentor_id)
        elif data.startswith('remove_mentor_telegram_'):
            mentor_id = int(data.replace('remove_mentor_telegram_', ''))
            await self.bot.mentor_handlers.remove_mentor_field(query, user_id, mentor_id, 'telegram')
        elif data.startswith('remove_mentor_instagram_'):
            mentor_id = int(data.replace('remove_mentor_instagram_', ''))
            await self.bot.mentor_handlers.remove_mentor_field(query, user_id, mentor_id, 'instagram')
        elif data.startswith('send_activation_'):
            mentor_id = int(data.replace('send_activation_', ''))
            await self.bot.mentor_handlers.send_activation_link(query, mentor_id)
        # Загальний edit_mentor_ в кінці
        elif data.startswith('edit_mentor_'):
            mentor_id = int(data.replace('edit_mentor_', ''))
            await self.bot.mentor_handlers.show_edit_mentor_menu(query, user_id, mentor_id)
        elif data.startswith('del_mentor_'):
            mentor_id = data.replace('del_mentor_', '')
            await self.bot.mentor_handlers.confirm_delete_mentor(query, mentor_id)
        elif data.startswith('confirm_del_mentor_'):
            mentor_id = data.replace('confirm_del_mentor_', '')
            await self.bot.mentor_handlers.delete_mentor(query, mentor_id)
        elif data.startswith('restore_mentor_'):
            mentor_id = data.replace('restore_mentor_', '')
            await self.bot.mentor_handlers.restore_mentor(query, mentor_id)
        elif data == 'add_mentor_additional_data':
            await self.bot.mentor_handlers.show_mentor_additional_data_menu(query, user_id)
        elif data == 'finish_mentor_adding':
            await self.bot.mentor_handlers.finish_mentor_adding(query, user_id)
        elif data == 'add_mentor_telegram':
            await self.bot.mentor_handlers.start_add_mentor_telegram(query, user_id)
        elif data == 'add_mentor_instagram':
            await self.bot.mentor_handlers.start_add_mentor_instagram(query, user_id)
        
        # Призначення ментора
        elif data.startswith('assign_mentor_'):
            streamer_id = data.replace('assign_mentor_', '')
            await self.bot.streamer_handlers.show_mentor_selection(query, user_id, streamer_id)
        elif data.startswith('select_mentor_'):
            # Формат: select_mentor_{streamer_id}_{mentor_name}
            remaining = data.replace('select_mentor_', '')
            parts = remaining.split('_', 1)
            if len(parts) == 2:
                streamer_id = parts[0]
                mentor_name = parts[1]
                logging.info(f"Assigning mentor - streamer_id: {streamer_id}, mentor_name: {mentor_name}")
                await self.bot.streamer_handlers.assign_mentor_to_streamer(query, user_id, streamer_id, mentor_name)
            else:
                logging.error(f"Invalid select_mentor_ format: {data}")
                await query.answer("❌ Помилка формату даних!", show_alert=True)
            
        # Noop
        elif data == 'noop':
            pass
            
        # Копіювання посилань (просто answer для feedback)
        elif data.startswith('copy_profile_'):
            await query.answer("📋 Посилання на профіль скопійовано!", show_alert=True)
        elif data.startswith('copy_telegram_'):
            await query.answer("📋 Посилання Telegram скопійовано!", show_alert=True)
        elif data.startswith('copy_instagram_'):
            await query.answer("📋 Посилання Instagram скопійовано!", show_alert=True)
    
    async def _handle_month_selection(self, query, user_id, data):
        """Обробка вибору місяця"""
        month_str = data.replace('month_', '')
        
        if '_' in month_str:
            parts = month_str.split('_')
            year = int(parts[0])
            month = int(parts[1])
        else:
            month = int(month_str)
            year = self.bot.temp_data.get(user_id, {}).get('selected_year')
        
        if year:
            await self.bot.streamer_handlers.show_streamers_by_month(query, year, month)
        else:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='filter_by_month')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Помилка: рік не знайдено. Спробуйте ще раз.",
                reply_markup=reply_markup
            )
