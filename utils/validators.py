"""
Утиліти для валідації даних
"""
import re
from typing import Optional, Tuple


def validate_tango_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Валідація URL профілю Tango
    
    Returns:
        (is_valid, user_id, clean_url)
    """
    # Шаблони для розпізнавання URL
    patterns = [
        r'tango\.me/([a-zA-Z0-9_-]+)',
        r'tango\.me/profile/([a-zA-Z0-9_-]+)',
        r'([a-zA-Z0-9_-]{4,})'  # Просто ID
    ]
    
    url = url.strip()
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            user_id = match.group(1)
            clean_url = f"https://www.tango.me/{user_id}"
            return True, user_id, clean_url
    
    return False, None, None


def validate_telegram_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Валідація Telegram URL або username
    
    Returns:
        (is_valid, username, clean_url)
    """
    url = url.strip()
    
    # Шаблони для Telegram
    patterns = [
        r't\.me/([a-zA-Z0-9_]{5,})',
        r'telegram\.me/([a-zA-Z0-9_]{5,})',
        r'@([a-zA-Z0-9_]{5,})',
        r'^([a-zA-Z0-9_]{5,})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            clean_url = f"https://t.me/{username}"
            return True, username, clean_url
    
    return False, None, None


def validate_instagram_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Валідація Instagram URL
    
    Returns:
        (is_valid, clean_url)
    """
    url = url.strip()
    
    # Шаблони для Instagram
    patterns = [
        r'instagram\.com/([a-zA-Z0-9_.]+)',
        r'@([a-zA-Z0-9_.]+)',
        r'^([a-zA-Z0-9_.]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            clean_url = f"https://www.instagram.com/{username}/"
            return True, clean_url
    
    return False, None


def sanitize_user_id(user_id: str) -> str:
    """Очищення user_id від зайвих символів"""
    # Видаляємо всі символи крім букв, цифр, підкреслень та дефісів
    return re.sub(r'[^a-zA-Z0-9_-]', '', user_id)


def is_valid_search_query(query: str) -> bool:
    """Перевірка валідності пошукового запиту"""
    query = query.strip()
    
    # Мінімальна довжина
    if len(query) < 2:
        return False
    
    # Перевірка що не тільки спецсимволи
    if re.match(r'^[^\w\s]+$', query):
        return False
    
    return True


def normalize_name(name: str) -> str:
    """Нормалізація імені користувача"""
    # Видаляємо зайві пробіли
    name = ' '.join(name.split())
    
    # Обмежуємо довжину
    if len(name) > 100:
        name = name[:100]
    
    return name.strip()
