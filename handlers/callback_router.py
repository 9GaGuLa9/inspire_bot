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
        
        # Обробка застарілих callback'ів
        try:
            await query.answer()
        except Exception as e:
            # Якщо callback застарів, просто ігноруємо
            if "Query is too old" in str(e) or "query id is invalid" in str(e):
                logging.warning(f"Ignored old callback query: {e}")
                return
            else:
                # Інші помилки логуємо
                logging.error(f"Error answering callback: {e}")
                return
        
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
        elif data == 'get_streamer_id':
            await self.bot.streamer_handlers.start_get_id(query, user_id)
        elif data == 'add_to_base_select':
            await self.bot.streamer_handlers.show_add_to_base_select(query, user_id)
        elif data == 'add_to_base_streamer':
            await self.bot.streamer_handlers.add_to_base_as_streamer(query, user_id)
        elif data == 'add_to_base_gifter':
            await self.bot.gifter_handlers.add_to_base_as_gifter(query, user_id)
        elif data == 'add_to_base_mentor':
            await self.bot.mentor_handlers.add_to_base_as_mentor(query, user_id)

        # Користувачі бота
        elif data == 'bot_users_menu':
            await self.bot.bot_users_handlers.show_bot_users_menu(query, user_id)
        elif data == 'add_bot_user':
            await self.bot.bot_users_handlers.start_add_user(query, user_id)
        elif data == 'list_bot_users':
            await self.bot.bot_users_handlers.show_users_list(query)
        elif data == 'change_user_role_select':
            await self.bot.bot_users_handlers.show_users_for_role_change(query)
        elif data == 'delete_bot_user_select':
            await self.bot.bot_users_handlers.show_users_for_deletion(query)

        # Створення запрошень
        elif data.startswith('create_invite_'):
            role = data.split('_')[2]
            await self.bot.bot_users_handlers.create_invitation_link(query, user_id, role)

        # Підтвердження активації
        elif data.startswith('confirm_activation_'):
            activation_code = data.replace('confirm_activation_', '')
            await self.bot.bot_users_handlers.confirm_activation(query, activation_code)

        elif data == 'decline_activation':
            await self.bot.bot_users_handlers.decline_activation(query)

        # Призначення ролі новому користувачу
        elif data.startswith('set_role_'):
            parts = data.split('_')
            role = parts[2]
            target_user_id = int(parts[3])
            await self.bot.bot_users_handlers.assign_role(query, user_id, role, target_user_id)

        # Вибір ролі для нового користувача (за username)
        elif data.startswith('select_role_'):
            parts = data.replace('select_role_', '').split('|', 1)
            role = parts[0]
            username = parts[1] if len(parts) > 1 else None
            if username:
                await self.bot.bot_users_handlers.confirm_role_and_send_invite(query, user_id, role, username)

        # Відправка запрошення
        elif data.startswith('send_invite_'):
            parts = data.replace('send_invite_', '').rsplit('|', 1)
            username = parts[0]
            role = parts[1] if len(parts) > 1 else None
            if username and role:
                await self.bot.bot_users_handlers.send_invite_to_user(query, user_id, username, role)

        # Додавання без запрошення
        elif data.startswith('skip_invite_'):
            parts = data.replace('skip_invite_', '').rsplit('|', 1)
            username = parts[0]
            role = parts[1] if len(parts) > 1 else None
            if username and role:
                await self.bot.bot_users_handlers.add_user_without_invite(query, user_id, username, role)

        # Зміна ролі існуючого користувача
        elif data.startswith('change_role_') and not data.startswith('change_role_select'):
            # Обробка інактивного користувача без telegram_id
            if data.startswith('change_role_inactive_'):
                username = data.replace('change_role_inactive_', '')
                target_user = self.bot.db.get_bot_user_by_username(username)
                if target_user:
                    await self.bot.bot_users_handlers.change_user_role_by_username(
                        query, user_id, username
                    )
                else:
                    await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            try:
                target_user_id = int(data.split('_')[2])
                await self.bot.bot_users_handlers.change_user_role(query, user_id, target_user_id)
            except (ValueError, IndexError):
                await query.answer("❌ Помилка: невірний користувач!", show_alert=True)

        elif data.startswith('update_role_'):
            # Обробка оновлення ролі для інактивного користувача
            if data.startswith('update_role_') and '_inactive_' in data:
                parts = data.split('_inactive_')
                role_part = parts[0].replace('update_role_', '')
                username = parts[1] if len(parts) > 1 else None
                
                if username:
                    target_user = self.bot.db.get_bot_user_by_username(username)
                    if target_user:
                        await self.bot.bot_users_handlers.update_user_role_by_username(
                            query, role_part, username
                        )
                    else:
                        await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            # Обробка оновлення ролі для активного користувача
            try:
                parts = data.split('_')
                new_role = parts[2]
                target_user_id = int(parts[3])
                await self.bot.bot_users_handlers.update_user_role(query, new_role, target_user_id)
            except (ValueError, IndexError):
                await query.answer("❌ Помилка: невірний користувач!", show_alert=True)

        # Видалення користувача
        elif data.startswith('confirm_delete_user_'):
            # Обробка інактивного користувача
            if data.startswith('confirm_delete_user_inactive_'):
                username = data.replace('confirm_delete_user_inactive_', '')
                target_user = self.bot.db.get_bot_user_by_username(username)
                if target_user:
                    await self.bot.bot_users_handlers.confirm_delete_user_by_username(
                        query, username
                    )
                else:
                    await query.answer("❌ Користувача не знайдено!", show_alert=True)
                return
            
            try:
                target_user_id = int(data.split('_')[3])
                await self.bot.bot_users_handlers.confirm_delete_user(query, target_user_id)
            except (ValueError, IndexError):
                await query.answer("❌ Помилка: невірний користувач!", show_alert=True)

        elif data.startswith('delete_user_confirmed_inactive_'):
            username = data.replace('delete_user_confirmed_inactive_', '')
            target_user = self.bot.db.get_bot_user_by_username(username)
            if target_user:
                await self.bot.bot_users_handlers.delete_user_by_username(query, username)
            else:
                await query.answer("❌ Користувача не знайдено!", show_alert=True)
            return

        elif data.startswith('delete_user_confirmed_'):
            try:
                target_user_id = int(data.split('_')[3])
                await self.bot.bot_users_handlers.delete_user(query, target_user_id)
            except (ValueError, IndexError):
                await query.answer("❌ Помилка: невірний користувач!", show_alert=True)


        # Стрімери
        elif data == 'add_streamer':
            await self.bot.streamer_handlers.start_add_streamer(query, user_id)
        elif data == 'remove_streamer':
            await self.bot.streamer_handlers.start_remove_streamer(query, user_id)
        elif data == 'show_streamers':
            await self.bot.streamer_handlers.show_all_streamers(query)
        elif data == 'search_streamer':
            await self.bot.streamer_handlers.start_search_streamer(query, user_id)
        elif data == 'update_diamonds_now':
            await self.bot.diamonds_handlers.start_update_diamonds(update, context)
            
        # Фільтрація
        elif data == 'filter_streamers':
            await self.bot.streamer_handlers.show_filter_menu(query, user_id)
        elif data == 'filter_by_year':
            await self.bot.streamer_handlers.show_year_selection(query, user_id)
        elif data == 'filter_by_month':
            await self.bot.streamer_handlers.show_year_selection_for_month(query, user_id)
        elif data == 'filter_by_mentor':
            await self.bot.streamer_handlers.show_mentor_filter_selection(query, user_id)
        elif data == 'filter_no_mentor':
            await self.bot.streamer_handlers.show_streamers_without_mentor(query)
        elif data == 'show_statistics':
            await self.bot.streamer_handlers.show_statistics(query)

        # Додаткові фільтри
        elif data == 'add_mentor_filter':
            await self.bot.streamer_handlers.show_mentor_selection_for_date_filter(query, user_id)
        elif data == 'add_year_filter':
            await self.bot.streamer_handlers.show_year_selection_for_mentor_filter(query, user_id)
        elif data == 'add_month_filter':
            await self.bot.streamer_handlers.show_month_selection_for_mentor_filter(query, user_id)

        # Скидання фільтрів
        elif data == 'reset_filters':
            if user_id in self.bot.temp_data:
                self.bot.temp_data[user_id].pop('filter_year', None)
                self.bot.temp_data[user_id].pop('filter_month', None)
                self.bot.temp_data[user_id].pop('filter_mentor', None)
            await self.bot.streamer_handlers.show_filter_menu(query, user_id)

        # Вибір ментора для фільтру
        elif data.startswith('filter_mentor_'):
            mentor_name = data.replace('filter_mentor_', '')
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['filter_mentor'] = mentor_name
            await self.bot.streamer_handlers.show_streamers_by_mentor(query, user_id, mentor_name)

        # Додавання року до існуючого фільтру
        elif data.startswith('add_year_'):
            year = int(data.replace('add_year_', ''))
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['filter_year'] = year
            self.bot.temp_data[user_id]['filter_month'] = None
            
            mentor_filter = self.bot.temp_data[user_id].get('filter_mentor')
            if mentor_filter:
                await self.bot.streamer_handlers.show_streamers_by_mentor(query, user_id, mentor_filter)
            else:
                await self.bot.streamer_handlers.show_streamers_by_year(query, year)

        # Додавання місяця до існуючого фільтру
        elif data.startswith('add_month_'):
            month = int(data.replace('add_month_', ''))
            filters = self.bot.temp_data.get(user_id, {})
            year = filters.get('filter_year')
            
            if year:
                if user_id not in self.bot.temp_data:
                    self.bot.temp_data[user_id] = {}
                self.bot.temp_data[user_id]['filter_month'] = month
                
                mentor_filter = self.bot.temp_data[user_id].get('filter_mentor')
                if mentor_filter:
                    await self.bot.streamer_handlers.show_streamers_by_mentor(query, user_id, mentor_filter)
                else:
                    await self.bot.streamer_handlers.show_streamers_by_month(query, year, month)
            
        # Роки та місяці
        elif data.startswith('year_for_month_'):
            year = int(data.replace('year_for_month_', ''))
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['selected_year'] = year
            await self.bot.streamer_handlers.show_month_selection(query, user_id, year)

        elif data.startswith('back_to_months_'):
            year = int(data.replace('back_to_months_', ''))
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['selected_year'] = year
            # Очищаємо фільтр місяця при поверненні
            self.bot.temp_data[user_id].pop('filter_month', None)
            await self.bot.streamer_handlers.show_month_selection(query, user_id, year)

        elif data.startswith('year_'):
            year = int(data.replace('year_', ''))
            # Встановлюємо фільтр року
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['filter_year'] = year
            self.bot.temp_data[user_id]['filter_month'] = None
            await self.bot.streamer_handlers.show_streamers_by_year(query, year)

        elif data.startswith('month_'):
            await self._handle_month_selection(query, user_id, data)
            
        # Видалення та підтвердження
        elif data.startswith('del_streamer_'):
            await self.bot.streamer_handlers.delete_streamer(query, data.replace('del_streamer_', ''))
        elif data.startswith('confirm_delete_'):
            await self.bot.streamer_handlers.confirm_delete_streamer(query, data.replace('confirm_delete_', ''))
        elif data.startswith('del_gifter_'):
            await self.bot.gifter_handlers.delete_gifter(query, data.replace('del_gifter_', ''))
            
        # Дарувальники
        elif data == 'remove_gifter':
            await self.bot.gifter_handlers.start_remove_gifter(query, user_id)
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
            await self.bot.streamer_handlers.set_platform_new_streamer(query, user_id, 'iOS')
        elif data == 'platform_android':
            await self.bot.streamer_handlers.set_platform_new_streamer(query, user_id, 'Android')
            
        # Редагування стрімера
        elif data.startswith('edit_streamer_'):
            streamer_id = data.replace('edit_streamer_', '')
            await self.bot.streamer_handlers.show_streamer_details(query, streamer_id)
            
        # Редагування стрімера - проміжні екрани
        elif data.startswith('prompt_edit_name_'):
            streamer_id = data.replace('prompt_edit_name_', '')
            await self.bot.streamer_handlers.show_edit_name_prompt(query, user_id, streamer_id)
        elif data.startswith('prompt_edit_telegram_'):
            streamer_id = data.replace('prompt_edit_telegram_', '')
            await self.bot.streamer_handlers.show_edit_telegram_prompt(query, user_id, streamer_id)
        elif data.startswith('prompt_edit_instagram_'):
            streamer_id = data.replace('prompt_edit_instagram_', '')
            await self.bot.streamer_handlers.show_edit_instagram_prompt(query, user_id, streamer_id)
        elif data.startswith('prompt_edit_platform_'):
            streamer_id = data.replace('prompt_edit_platform_', '')
            await self.bot.streamer_handlers.show_edit_platform_prompt(query, user_id, streamer_id)

        # Видалення полів
        elif data.startswith('delete_telegram_'):
            streamer_id = data.replace('delete_telegram_', '')
            await self.bot.streamer_handlers.delete_telegram(query, streamer_id)
        elif data.startswith('delete_instagram_'):
            streamer_id = data.replace('delete_instagram_', '')
            await self.bot.streamer_handlers.delete_instagram(query, streamer_id)
        elif data.startswith('delete_platform_'):
            streamer_id = data.replace('delete_platform_', '')
            await self.bot.streamer_handlers.delete_platform(query, streamer_id)

        # Встановлення платформи
        elif data.startswith('set_platform_'):
            parts = data.replace('set_platform_', '').rsplit('_', 1)
            streamer_id = parts[0]
            platform = parts[1]
            await self.bot.streamer_handlers.set_platform(query, streamer_id, platform)

        elif data.startswith('confirm_rewrite_'):
            # Формат: confirm_rewrite_{old_id}_{new_id}
            parts = data.replace('confirm_rewrite_', '').split('_', 1)
            if len(parts) == 2:
                old_streamer_id = parts[0]
                new_streamer_id = parts[1]
                await self.bot.streamer_handlers.confirm_profile_rewrite(query, user_id, old_streamer_id, new_streamer_id)
                
        # Пагінація
        elif data.startswith('page_streamers_'):
            page = int(data.replace('page_streamers_', ''))
            await self.bot.streamer_handlers.show_all_streamers_paginated(query, page)
        elif data.startswith('page_delete_'):
            page = int(data.replace('page_delete_', ''))
            await self.bot.streamer_handlers.show_delete_page(query, user_id, page)
        
        # Ментори - СПЕЦИФІЧНІ CALLBACK СПОЧАТКУ!
        elif data == 'add_mentor':
            await self.bot.mentor_handlers.start_add_mentor(query, user_id)
        elif data == 'add_mentor_telegram':
            await self.bot.mentor_handlers.start_add_mentor_telegram(query, user_id)
        elif data == 'confirm_mentor_telegram':
            await self.bot.mentor_handlers.confirm_mentor_telegram_add(query, user_id)
        elif data == 'add_mentor_instagram':
            await self.bot.mentor_handlers.start_add_mentor_instagram(query, user_id)
        elif data == 'add_mentor_additional_data':
            await self.bot.mentor_handlers.show_mentor_additional_data_menu(query, user_id)
        elif data == 'finish_mentor_adding':
            await self.bot.mentor_handlers.finish_mentor_adding(query, user_id)
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
        
        # Призначення ментора
        elif data.startswith('assign_mentor_'):
            streamer_id = data.replace('assign_mentor_', '')
            await self.bot.streamer_handlers.show_mentor_selection(query, user_id, streamer_id)
        elif data.startswith('select_mentor_'):
            # Формат: select_mentor_{streamer_id}_{mentor_id}
            # ВАЖЛИВО: streamer_id може містити символ "_"!
            remaining = data.replace('select_mentor_', '')
            parts = remaining.rsplit('_', 1)  # ← rsplit розділяє з КІНЦЯ!
            if len(parts) == 2:
                streamer_id = parts[0]  # Може містити "_"
                mentor_id = parts[1]    # Завжди число
                logging.info(f"Assigning mentor - streamer_id: {streamer_id}, mentor_id: {mentor_id}")
                await self.bot.streamer_handlers.assign_mentor_to_streamer(query, user_id, streamer_id, mentor_id)
            else:
                logging.error(f"Invalid select_mentor_ format: {data}")
                await query.answer("❌ Помилка формату даних!", show_alert=True)
        
        # Додавання ментора до існуючого фільтру - НАПРИКІНЦІ
        elif data.startswith('add_mentor_'):
            mentor_name = data.replace('add_mentor_', '')
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['filter_mentor'] = mentor_name
            
            # Повертаємось до відображення з оновленим фільтром
            filters = self.bot.temp_data[user_id]
            year = filters.get('filter_year')
            month = filters.get('filter_month')
            
            if year and month:
                await self.bot.streamer_handlers.show_streamers_by_month(query, year, month)
            elif year:
                await self.bot.streamer_handlers.show_streamers_by_year(query, year)
            else:
                await self.bot.streamer_handlers.show_streamers_by_mentor(query, user_id, mentor_name)

        # Показ окремих меню для Telegram/Instagram ментора
        elif data.startswith('show_mentor_telegram_'):
            mentor_id = int(data.replace('show_mentor_telegram_', ''))
            await self.bot.mentor_handlers.show_mentor_telegram_menu(query, user_id, mentor_id)
        elif data.startswith('show_mentor_instagram_'):
            mentor_id = int(data.replace('show_mentor_instagram_', ''))
            await self.bot.mentor_handlers.show_mentor_instagram_menu(query, user_id, mentor_id)

        # Видалення Telegram/Instagram ментора
        elif data.startswith('delete_mentor_telegram_'):
            mentor_id = int(data.replace('delete_mentor_telegram_', ''))
            await self.bot.mentor_handlers.delete_mentor_telegram(query, mentor_id)
        elif data.startswith('delete_mentor_instagram_'):
            mentor_id = int(data.replace('delete_mentor_instagram_', ''))
            await self.bot.mentor_handlers.delete_mentor_instagram(query, mentor_id)
            
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
            # Встановлюємо фільтри
            if user_id not in self.bot.temp_data:
                self.bot.temp_data[user_id] = {}
            self.bot.temp_data[user_id]['filter_year'] = year
            self.bot.temp_data[user_id]['filter_month'] = month
            
            await self.bot.streamer_handlers.show_streamers_by_month(query, year, month)
        else:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='filter_by_month')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Помилка: рік не знайдено. Спробуйте ще раз.",
                reply_markup=reply_markup
            )