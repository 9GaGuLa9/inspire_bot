"""
Handler'и для пошуку дарувальників у стрімах
"""
import logging
import os
from datetime import datetime
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup


class SearchHandlers:
    """Обробка пошуку дарувальників"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def start_search_gifters(self, query, user_id):
        """Початок пошуку дарувальників"""
        gifters = self.bot.db.get_all_gifters()
        if not gifters:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ База дарувальників порожня!\n\nСпочатку додайте дарувальників через меню бази користувачів.",
                reply_markup=reply_markup
            )
            return
        
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {}
        self.bot.temp_data[user_id]['selected_gifters'] = []
        
        await self.show_gifter_selection(query, user_id)

    async def toggle_gifter_selection(self, query, user_id, gifter_id):
        """Переключення вибору дарувальника"""
        if user_id not in self.bot.temp_data:
            self.bot.temp_data[user_id] = {'selected_gifters': []}
        
        selected_ids = self.bot.temp_data[user_id]['selected_gifters']
        
        if gifter_id in selected_ids:
            selected_ids.remove(gifter_id)
        else:
            selected_ids.append(gifter_id)
        
        await self.show_gifter_selection(query, user_id)

    async def execute_search(self, query, user_id):
        """Виконання пошуку дарувальників"""
        selected_ids = self.bot.temp_data.get(user_id, {}).get('selected_gifters', [])
        
        if not selected_ids:
            await query.edit_message_text("❌ Не обрано жодного дарувальника!")
            return
        
        await query.edit_message_text(
            f"🔍 Розпочинаю пошук...\n\n"
            f"Дарувальників для пошуку: {len(selected_ids)}\n"
            f"Це може зайняти кілька хвилин...\n\n"
            f"**УВАГА:** Може відкритися браузер для авторизації на Tango.me"
        )
        
        try:
            with GifterSearcher() as searcher:
                results = searcher.search_gifters(
                    gifter_ids=selected_ids,
                    num_streamers=100,
                    categories=["Popular", "Recommended"]
                )
                
                if results.get("found_gifters"):
                    save_path = searcher.save_results(results)
                    report = self.format_search_report(results, save_path)
                    await self.send_search_results(query, report, results)
                else:
                    keyboard = [[InlineKeyboardButton("🔍 Новий пошук", callback_data='search_gifters')],
                                [InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"😔 Пошук завершено\n\n"
                        f"📊 Перевірено стрімерів: {results.get('searched_streamers', 0)}\n"
                        f"🎯 Знайдено збігів: 0\n\n"
                        f"Спробуйте пізніше або оберіть інших дарувальників.",
                        reply_markup=reply_markup
                    )
        
        except Exception as ex:
            logging.error(f"Помилка пошуку: {ex}")
            keyboard = [[InlineKeyboardButton("🔍 Спробувати знову", callback_data='search_gifters')],
                        [InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ Помилка під час пошуку:\n{str(ex)}\n\nСпробуйте пізніше.\n\n"
                f"**Можливі причини:**\n"
                f"• Проблеми з інтернет-з'єднанням\n"
                f"• Потрібна повторна авторизація на Tango.me\n"
                f"• Сайт Tango.me тимчасово недоступний",
                reply_markup=reply_markup
            )
        
        if user_id in self.bot.temp_data:
            del self.bot.temp_data[user_id]

    def format_search_report(self, results: Dict, save_path: str = None) -> str:
        """Форматування звіту про пошук"""
        found_count = results.get('total_found', 0)
        searched_streamers = results.get('searched_streamers', 0)
        categories = ", ".join(results.get('categories_searched', []))
        search_time = results.get('search_time', 'невідомо')
        
        report = f"✅ **Пошук завершено успішно!**\n\n"
        report += f"📊 **Статистика:**\n"
        report += f"• Знайдено збігів: {found_count}\n"
        report += f"• Перевірено стрімерів: {searched_streamers}\n"
        report += f"• Категорії: {categories}\n"
        report += f"• Час пошуку: {search_time}\n"
        
        if save_path:
            report += f"• Файл збережено: `{os.path.basename(save_path)}`\n"
        
        if found_count > 0:
            report += f"\n🎯 **Знайдені збіги:**\n"
            
            gifters_found = {}
            for item in results.get('found_gifters', []):
                gifter_name = item.get('Ім`я дарувальника', 'Невідомо')
                streamer_name = item.get('Ім`я стрімера', 'Невідомо')
                coins = item.get('Кількість монет', '0')
                stream_url = item.get('Посилання на стрім', '')
                
                if gifter_name not in gifters_found:
                    gifters_found[gifter_name] = []
                
                gifters_found[gifter_name].append({
                    'streamer': streamer_name,
                    'coins': coins,
                    'url': stream_url
                })
            
            for gifter_name, streams in gifters_found.items():
                report += f"\n🎁 **{gifter_name}**\n"
                for stream_info in streams[:3]:
                    coins_text = f" ({stream_info['coins']} монет)" if stream_info['coins'] != 'Глядач' else ' (глядач)'
                    report += f"  └ {stream_info['streamer']}{coins_text}\n"
                
                if len(streams) > 3:
                    report += f"  └ ... і ще {len(streams) - 3} стрімів\n"
        
        return report

    async def send_search_results(self, query, report: str, results: Dict):
        """Надсилання результатів пошуку"""
        keyboard = [
            [InlineKeyboardButton("🔍 Новий пошук", callback_data='search_gifters')],
            [InlineKeyboardButton("◀️ Головне меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if len(report) > 4000:
            parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
            
            await query.edit_message_text(
                parts[0],
                parse_mode='Markdown',
                reply_markup=reply_markup if len(parts) == 1 else None,
                disable_web_page_preview=True
            )
            
            for i, part in enumerate(parts[1:], 1):
                await query.message.reply_text(
                    part,
                    parse_mode='Markdown',
                    reply_markup=reply_markup if i == len(parts) - 1 else None,
                    disable_web_page_preview=True
                )
        else:
            await query.edit_message_text(
                report,
                parse_mode='Markdown',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

