"""
Конфігураційний файл — завантажує налаштування з .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ================================
# ТОКЕН БОТА ТА ВЛАСНИК
# ================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ================================
# GOOGLE SHEETS
# ================================
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/service_account.json")
GOOGLE_SHEET_NAME = "Inspire_agency"

# Назви аркушів
SHEET_STREAMERS = "Стрімери"
SHEET_MENTORS = "Ментори"
SHEET_GIFTERS = "Дарувальники"
SHEET_ERRORS = "Помилки"

# Затримка між запитами до Google Sheets (секунди)
SHEETS_SYNC_INTERVAL = 30

# ================================
# ШЛЯХИ ДО ФАЙЛІВ
# ================================
DB_NAME = 'tango_bot.db'
SEARCH_RESULTS_DIR = 'search_results'

# ================================
# КОНСТАНТИ ДЛЯ ПАГІНАЦІЇ
# ================================
STREAMERS_PER_PAGE = 10
DELETE_ITEMS_PER_PAGE = 10

# ================================
# СЛОВНИК МІСЯЦІВ
# ================================
MONTHS_UA = {
    1: 'Січень', 2: 'Лютий', 3: 'Березень', 4: 'Квітень',
    5: 'Травень', 6: 'Червень', 7: 'Липень', 8: 'Серпень',
    9: 'Вересень', 10: 'Жовтень', 11: 'Листопад', 12: 'Грудень'
}

# ================================
# СИСТЕМА РОЛЕЙ
# ================================
ROLES = {
    'owner': 'Власник',
    'superadmin': 'Суперадмін',
    'admin': 'Адмін',
    'mentor': 'Ментор',
    'guest': 'Гість'
}

ROLE_HIERARCHY = {
    'owner': 5,
    'superadmin': 4,
    'admin': 3,
    'mentor': 2,
    'guest': 1
}

ROLE_EMOJI = {
    'owner': '👑',
    'superadmin': '⭐',
    'admin': '🔷',
    'mentor': '🎯',
    'guest': '👤'
}

# ================================
# ДІАМАНТИ
# ================================
DIAMONDS_API_URL = (
    "https://gateway.tango.me/proxycador/api/profiles/v2/single"
    "?id={user_id}&basicProfile=true&liveStats=true&followStats=true"
)
DIAMONDS_REQUEST_DELAY = 0.5   # секунди між запитами
DIAMONDS_MAX_RETRIES = 3       # кількість спроб при помилці

# ================================
# НАЛАШТУВАННЯ СПОВІЩЕНЬ
# ================================
NOTIFICATIONS = {
    'new_streamer_to_admins': True,
    'streamer_reassigned': True,
    'new_user_role': True,
}

# ================================
# НАЛАШТУВАННЯ АУДИТ-ЛОГУ
# ================================
AUDIT_LOG = {
    'max_records': 10000,
    'enabled_actions': [
        'add_streamer', 'edit_streamer', 'delete_streamer',
        'assign_mentor', 'reassign_mentor',
        'add_donor', 'delete_donor',
        'add_user', 'edit_user', 'delete_user', 'role_change',
        'diamonds_update', 'monthly_diamonds_update',
    ]
}

# ================================
# ТЕКСТОВІ ПОВІДОМЛЕННЯ
# ================================
HELP_TEXT = """
ℹ️ <b>Інструкція по використанню</b>

<b>🗂 База користувачів:</b>
• <b>Стрімери</b> — профілі з Telegram, Instagram, платформою, діамантами
• <b>Дарувальники</b> — для пошуку в стрімах

<b>💎 Діаманти:</b>
• Ручне оновлення — кнопка в меню стрімерів
• Автооновлення — щомісяця в останній день о 00:00 UTC

<b>👥 Система ролей:</b>
• Різні рівні доступу
• Управління командою менторів
• Аудит-лог всіх дій
"""

START_MESSAGE = "🤖 Вітаю в Tango Bot!\n\nОберіть дію:"

# ================================
# ЛОГУВАННЯ
# ================================
LOG_FILE = 'bot.log'
LOG_LEVEL = 'INFO'
