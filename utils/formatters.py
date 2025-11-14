"""
Утиліти для форматування повідомлень
"""
import os
from typing import Dict, List


def format_streamer_info(streamer_data: Dict, position: int = None) -> str:
    """Форматування інформації про стрімера"""
    name = streamer_data.get('name', 'Без імені')
    user_id = streamer_data.get('user_id', '')
    profile_url = streamer_data.get('profile_url', '')
    tg_name = streamer_data.get('tg_name')
    tg_url = streamer_data.get('tg_url')
    instagram_url = streamer_data.get('instagram_url')
    platform = streamer_data.get('platform')
    created_at = streamer_data.get('created_at', '')
    
    # Форматування дати
    if created_at:
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(created_at)
            date_str = date_obj.strftime('%d.%m.%Y %H:%M')
        except:
            date_str = created_at
    else:
        date_str = 'невідомо'
    
    # Базова інформація
    if position:
        info = f"**{position}. {name}**\n"
    else:
        info = f"**{name}**\n"
    
    info += f"└ ID: `{user_id}`\n"
    info += f"└ [Профіль Tango]({profile_url})\n"
    
    # Додаткова інформація
    if tg_name or tg_url:
        tg_display = f"@{tg_name}" if tg_name else "посилання"
        tg_link = tg_url if tg_url else f"https://t.me/{tg_name}"
        info += f"└ Telegram: [{tg_display}]({tg_link})\n"
    
    if instagram_url:
        info += f"└ [Instagram]({instagram_url})\n"
    
    if platform:
        emoji = "🍎" if platform.lower() == 'ios' else "🤖"
        info += f"└ Платформа: {emoji} {platform}\n"
    
    info += f"└ Додано: {date_str}\n"
    
    return info


def format_gifter_info(gifter_data: Dict, position: int = None) -> str:
    """Форматування інформації про дарувальника"""
    name = gifter_data.get('name', 'Без імені')
    user_id = gifter_data.get('user_id', '')
    profile_url = gifter_data.get('profile_url', '')
    
    if position:
        info = f"**{position}. {name}**\n"
    else:
        info = f"**{name}**\n"
    
    info += f"└ ID: `{user_id}`\n"
    info += f"└ [Профіль Tango]({profile_url})\n"
    
    return info


def format_search_report(results: Dict, save_path: str = None) -> str:
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


def format_statistics(stats: Dict, period_stats: Dict) -> str:
    """Форматування статистики"""
    text = "📊 **Статистика бази даних**\n\n"
    
    streamers_count = stats.get('streamers_count', 0)
    gifters_count = stats.get('gifters_count', 0)
    first_date = stats.get('first_streamer_date', 'немає даних')
    last_date = stats.get('last_streamer_date', 'немає даних')
    
    text += f"👥 **Стрімерів:** {streamers_count}\n"
    text += f"🎁 **Дарувальників:** {gifters_count}\n\n"
    
    if first_date != 'немає даних':
        try:
            from datetime import datetime
            first_obj = datetime.fromisoformat(first_date)
            last_obj = datetime.fromisoformat(last_date)
            text += f"📅 **Перший запис:** {first_obj.strftime('%d.%m.%Y')}\n"
            text += f"📅 **Останній запис:** {last_obj.strftime('%d.%m.%Y')}\n\n"
        except:
            pass
    
    if period_stats:
        text += "📈 **Додано стрімерів по місяцях:**\n"
        
        from config import MONTHS_UA
        
        for period, count in list(period_stats.items())[:12]:
            try:
                year, month = period.split('-')
                month_name = MONTHS_UA.get(int(month), month)
                text += f"• {month_name} {year}: {count}\n"
            except:
                text += f"• {period}: {count}\n"
    
    return text


def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """Розбиття довгих повідомлень на частини"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line + '\n'
        else:
            current_part += line + '\n'
    
    if current_part:
        parts.append(current_part)
    
    return parts
