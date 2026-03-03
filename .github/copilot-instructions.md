# Tango Bot - Инструкции для AI-агентов

## Архитектура проекта

Это Telegram-бот для управления стримерами и дарителями на платформе Tango, написанный с использованием `python-telegram-bot` и SQLite.

### Основные компоненты

**Слой приложения:**
- `bot.py` - основной класс `TangoBot`, инициализирует все handler'ы и сервисы
- `main.py` - точка входа, настраивает Application и регистрирует обработчики команд
- `config.py` - глобальные константы: BOT_TOKEN, OWNER_ID, роли, месяцы, emoji

**Слой данных:**
- `database_manager.py` - DatabaseManager для операций SQLite с контекстным менеджером `get_connection()`
- `database_schema.sql` - схема БД (таблицы: mentors, streamers, donors, bot_users, audit_log)

**Слой логики:**
- `services/tango_api_client.py` - клиент Tango API для получения данных стримеров
- `services/gifter_search.py` - поиск дарителей по критериям
- `utils/formatters.py` - форматирование сообщений и данных
- `utils/validators.py` - валидация входных данных

**Слой взаимодействия:**
- `handlers/callback_router.py` - маршрутизация всех callback_query по callback_data
- `handlers/*.py` - 11 handler классов для разных функций (меню, стримеры, дареватели и т.д.)

### Система управления состоянием

**В bot.py хранится:**
- `user_states: Dict[int, str]` - текущее состояние пользователя (напр., "waiting_new_user_id")
- `temp_data: Dict[int, Dict]` - временные данные между этапами диалога

**Пример потока:**
1. User нажимает кнопку → callback_router маршрутизирует
2. Handler устанавливает состояние: `bot.user_states[user_id] = 'waiting_mentor_name'`
3. Пользователь отправляет текст → `handle_message()` проверяет состояние и обрабатывает

### Система ролей (ROLE-BASED ACCESS CONTROL)

**Иерархия ролей (от низкого к высокому):**
```python
ROLE_HIERARCHY = {
    'guest': 1,      # базовый доступ
    'mentor': 2,     # может добавлять стримеров
    'admin': 3,      # управление ментором
    'superadmin': 4, # управление администраторами
    'owner': 5       # полный контроль (OWNER_ID из config.py)
}
```

**Использование:**
- Часто проверяется через `DatabaseManager.get_user_role(user_id)` 
- В handlers используется декоратор `@check_role(['admin', 'superadmin'])` из `role_decorators.py`
-각 handler принимает текущего пользователя и проверяет его роль перед выполнением действия

## Критические рабочие процессы

### Получение Telegram ID пользователя

Бот имеет встроенную команду `/myid` для получения ID:
- Пользователь пишет `/myid` боту
- Бот возвращает текущий ID в формате, удобном для копирования
- Обработчик: `myid_command_handler()` в `main.py`

При добавлении нового пользователя система автоматически предлагает использовать эту команду (см. `bot_users_handlers.start_add_user()`).

### Добавление нового пользователя (bot_users_handlers.py)

**Flow с запросом запрошения:**

1. Admin нажимает "➕ Додати користувача"
2. Бот просит Username (напр. `@username`)
3. Admin вводит username → устанавливается состояние `waiting_new_user_username`
4. Handler вызывает `show_role_selection_for_new_user()` → показывает выбор ролей
5. Admin выбирает роль (callback: `select_role_<role>_<username>`)
6. Вызывается `confirm_role_and_send_invite()` → спрашивает "Надіслати запрошення?"
7. **Если ДА:** вызывается `send_invite_to_user()` → генерирует activation_code, добавляет в БД со статусом **pending**, показывает ссылку активации
8. **Если НИ:** вызывается `add_user_without_invite()` → добавляет со статусом **inactive** (без запрошения)

**Статусы пользователей:**
- `inactive` - добавлен без запрошения, нет доступа
- `pending` - ждет активации через activation_code, нет доступа
- `active` - активирован, полный доступ

**Callback data для новых пользователей:**
- `select_role_<role>_<username>` - выбор роли
- `send_invite_<username>_<role>` - запрос подтверждения на отправку запрошения
- `skip_invite_<username>_<role>` - добавление без запрошения

**Активация пользователя:**
- User получает ссылку: `/start activate_<code>`
- Handler: `handle_user_activation(update, activation_code)`
- Метод БД: `activate_bot_user(activation_code, telegram_id)` → изменяет статус с pending→active, привязывает telegram_id

**Новые методы БД:**
- `add_bot_user_pending(username, role, added_by, activation_code)` - добавить pending пользователя
- `add_bot_user_by_username(username, role, added_by, status='inactive')` - добавить пользователя с указанным статусом
- `activate_bot_user(activation_code, telegram_id)` - активировать пользователя

### Работа со стримерами (streamer_handlers.py)

Типичный CRUD-цикл:
- **Create:** `db.add_streamer()` после валидации через `validators.validate_streamer_data()`
- **Read:** `db.get_all_streamers()` с пагинацией (см. STREAMERS_PER_PAGE)
- **Update:** `db.update_streamer()` → отправляет уведомление ментору
- **Delete:** `db.delete_streamer()` с записью в audit_log

### Активация ментора

1. Owner создает ссылку с activation_code: `/start mentor_<code>`
2. Ментор переходит по ссылке
3. `mentor_handlers.handle_mentor_activation()` проверяет код
4. Добавляет ментора в bot_users с ролью 'mentor'

## Соглашения по кодированию

### Структура обработчика

```python
class SomeHandlers:
    def __init__(self, bot):
        self.bot = bot
    
    async def show_menu(self, query):
        """Показать меню с кнопками"""
        keyboard = [[InlineKeyboardButton("Текст", callback_data='unique_id')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Сообщение", reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_action(self, query, user_id):
        """Обработать действие"""
        # 1. Валидация данных
        # 2. Операция с БД через self.bot.db
        # 3. Отправка ответа
        # 4. Очистка состояния если нужно
```

### Callback data соглашения

- `main_menu` - простые идентификаторы для меню
- `set_role_<role>_<user_id>` - параметризованные с разделителем `_`
- `delete_<item_type>_<item_id>` - для операций удаления

### Работа с БД

```python
# Всегда использовать контекстный менеджер
with self.bot.db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mentors WHERE telegram_chat_id = ?", (chat_id,))
    result = cursor.fetchone()

# ИЛИ использовать готовые методы DatabaseManager (предпочтительно)
user = self.bot.db.get_bot_user_by_telegram_id(user_id)
```

## Интеграции и зависимости

### Внешние API

- **Tango API** (`services/tango_api_client.py`):
  - Требует visitor_token (сохраняется в tango_token.json)
  - Auto-refresh если истёк (проверка: `_is_token_valid()`)
  - Основной метод: `search_gifters(filters)` для поиска дарителей

### Внешние сервисы

- **Telegram Bot API** через `python-telegram-bot` v20+
- **SQLite** для локального хранилища

### Файлы конфигурации

- `config.py` - всегда читай для констант (не hardcode!)
- `requirements.txt` - зависимости (python-telegram-bot, requests, etc.)

## Частые правки и точки расширения

### Добавление нового обработчика команд

1. Создай класс в `handlers/new_feature_handlers.py`
2. Инициализируй в `TangoBot.__init__()`
3. Добавь обработку в `callback_router.route_callback()` 
4. Привяжи в `main.py` через `CallbackQueryHandler()`

### Добавление таблицы в БД

1. Добавь CREATE TABLE в `database_manager.py.init_database()`
2. Добавь методы get/add/update/delete в DatabaseManager
3. Обнови `database_schema.sql` для документации

### Отправка уведомлений

Используй `notification_service.py`:
```python
await self.bot.notification_service.notify_admins(
    f"❗ {message}",
    include_owner=True
)
```

## Отладка и тестирование

### Запуск бота

```bash
# Убедись что BOT_TOKEN установлен в config.py
python main.py
```

### Просмотр логов

Логирование настроено в `main.py`:
```python
logging.basicConfig(level=logging.INFO)
```

### Тестирование handler'ов

- Используй @userinfobot в Telegram чтобы узнать свой ID
- Установи свой ID как OWNER_ID в config.py
- Проверь role_decorators для требований к ролям

## Трудные места в кодовой базе

1. **Дублирование callback data логики** - часть параметризованных callback'ов обработана в `route_callback()`, будь внимателен с форматом
2. **Состояние разбросано** - `user_states` и `temp_data` оба используются, убедись что очищаешь оба при необходимости
3. **Миграция БД** - есть старый путь `DB_FILE` и новый `DB_NAME`, для новых операций используй только `tango_bot.db`
4. **Token refresh в TangoAPIClient** - может занять время, не вызывай в горячем цикле
