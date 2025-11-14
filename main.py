"""
Головний файл запуску Tango Bot
"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN
from bot import TangoBot

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    """Запуск бота"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Помилка: Не встановлено токен бота!")
        print("Отримайте токен у @BotFather та змініть його в config.py")
        return
    
    # Створюємо екземпляр бота
    bot = TangoBot(BOT_TOKEN)
    
    # Створюємо application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("🤖 Tango Search Bot запущено!")
    print("\nНатисніть Ctrl+C для зупинки")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("\n👋 Бот зупинено")


if __name__ == '__main__':
    main()
