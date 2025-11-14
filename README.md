# Tango Bot - Модульна структура

## Структура

```
tango_bot/
├── main.py                    # Запуск бота
├── config.py                  # Константи і токен
├── bot.py                     # Основний клас
├── database_manager.py        # БД
├── handlers/                  # Обробники команд (ПОТРІБНА ІМПЛЕМЕНТАЦІЯ)
├── services/                  # API і пошук (✓ готові)
└── utils/                     # Утиліти (✓ готові)
```

## Що зробити

### 1. Налаштувати токен (1 хв)
```python
# config.py
BOT_TOKEN = "ВАШ_ТОКЕН_ТУТ"
```

### 2. Заповнити handler'и (30-60 хв)

Скопіюйте методи з `tango_bot_with_api.py` в:
- `handlers/streamer_handlers.py` - всі методи зі стрімерами
- `handlers/gifter_handlers.py` - методи з дарувальниками  
- `handlers/search_handlers.py` - методи пошуку

**При копіюванні замінити:**
- `self.db` → `self.bot.db`
- `self.temp_data` → `self.bot.temp_data`
- `self.user_states` → `self.bot.user_states`
- `self.api_client` → `self.bot.api_client`

### 3. Встановити залежності
```bash
pip install -r requirements.txt
```

### 4. Запустити
```bash
python main.py
```

## Готові модулі

✅ config.py
✅ database_manager.py
✅ services/tango_api_client.py
✅ services/gifter_search.py
✅ utils/formatters.py
✅ utils/validators.py
✅ handlers/menu_handlers.py
✅ handlers/callback_router.py

⚠️ handlers/streamer_handlers.py - заглушки
⚠️ handlers/gifter_handlers.py - заглушки
⚠️ handlers/search_handlers.py - заглушки
