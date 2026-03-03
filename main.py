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


async def start_command_handler(update, context):
    """Обробка команди /start з параметрами"""
    bot_instance = context.bot_data.get('bot_instance')
    
    # Перевіряємо чи є параметри (для активації)
    if context.args and len(context.args) > 0:
        param = context.args[0]
        
        # Активація користувача
        if param.startswith('activate_'):
            activation_code = param.replace('activate_', '')
            await bot_instance.bot_users_handlers.handle_user_activation(update, activation_code)
            return
        
        # Активація ментора
        if param.startswith('mentor_'):
            activation_code = param.replace('mentor_', '')
            await bot_instance.mentor_handlers.handle_mentor_activation(update, activation_code)
            return
    
    # Звичайний старт
    await bot_instance.start(update, context)


async def myid_command_handler(update, context):
    """Обробка команди /myid - відправка Telegram ID користувача"""
    user = update.effective_user
    
    # Копіюємо ID в формат, зручний для копіювання
    await update.message.reply_text(
        f"🆔 **Ваш Telegram ID:**\n\n`{user.id}`\n\n"
        f"_ID скопійовано в буфер обміну_",
        parse_mode='Markdown'
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
    
    # Зберігаємо application в bot для доступу до bot.get_me()
    bot.application = application
    
    # Зберігаємо екземпляр бота в bot_data для доступу з обробників
    application.bot_data['bot_instance'] = bot
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start_command_handler))
    application.add_handler(CommandHandler("myid", myid_command_handler))
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
