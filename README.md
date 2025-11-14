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

### 2. Встановити залежності
```bash
pip install -r requirements.txt
```

### 3. Запустити
```bash
python main.py
```

## Готові модулі

✅ config.py
✅ database_manager.py
✅ services/tango_api_client.py
⚠️ services/gifter_search.py
✅ utils/formatters.py
✅ utils/validators.py
✅ handlers/menu_handlers.py
✅ handlers/callback_router.py
✅ handlers/streamer_handlers.py
⚠️ handlers/gifter_handlers.py
✅ handlers/search_handlers.py
