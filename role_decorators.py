# role_decorators.py
# Декоратори для перевірки ролей користувачів

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import logging
import config

logger = logging.getLogger(__name__)


def check_role(allowed_roles):
    """
    Декоратор для перевірки ролі користувача.
    
    Args:
        allowed_roles: список дозволених ролей або мінімальна роль
    
    Usage:
        @check_role(['admin', 'superadmin', 'owner'])
        @check_role('admin')  # admin і всі вищі
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Перевіряємо чи користувач є в базі
            user = self.bot.db.get_user_by_telegram_id(user_id)
            
            if not user:
                logger.warning(f"Unauthorized access attempt from user_id: {user_id}")
                query = update.callback_query
                if query:
                    await query.answer("❌ У вас немає доступу до бота.", show_alert=True)
                else:
                    await update.message.reply_text(config.MESSAGES['access_denied'])
                return
            
            user_role = user['role']
            
            # Якщо передана одна роль як рядок - конвертуємо в список з урахуванням ієрархії
            if isinstance(allowed_roles, str):
                min_role_level = config.ROLE_HIERARCHY.get(allowed_roles, 0)
                allowed_roles_list = [
                    role for role, level in config.ROLE_HIERARCHY.items() 
                    if level >= min_role_level
                ]
            else:
                allowed_roles_list = allowed_roles
            
            # Перевіряємо доступ
            if user_role not in allowed_roles_list:
                logger.warning(
                    f"Access denied for user {user_id} ({user_role}) "
                    f"to function {func.__name__}. Required: {allowed_roles_list}"
                )
                query = update.callback_query
                if query:
                    await query.answer(config.MESSAGES['access_denied'], show_alert=True)
                else:
                    await update.message.reply_text(config.MESSAGES['access_denied'])
                return
            
            # Додаємо роль користувача в kwargs для використання в обробнику
            kwargs['user_role'] = user_role
            kwargs['user_data'] = user
            
            return await func(self, update, context, *args, **kwargs)
        
        return wrapper
    return decorator


def owner_only(func):
    """Декоратор: тільки для Власника"""
    return check_role(['owner'])(func)


def superadmin_or_higher(func):
    """Декоратор: Суперадмін і вище"""
    return check_role('superadmin')(func)


def admin_or_higher(func):
    """Декоратор: Адмін і вище"""
    return check_role('admin')(func)


def mentor_or_higher(func):
    """Декоратор: Ментор і вище"""
    return check_role('mentor')(func)


def any_authenticated(func):
    """Декоратор: будь-який авторизований користувач (включно з гостем)"""
    return check_role(['owner', 'superadmin', 'admin', 'mentor', 'guest'])(func)


def can_manage_role(manager_role, target_role):
    """
    Перевіряє чи може користувач з manager_role керувати користувачем з target_role.
    
    Правила:
    - owner може керувати всіма
    - superadmin може керувати admin, mentor, guest
    - admin може керувати mentor, guest
    - mentor не може керувати нікім
    - guest не може керувати нікім
    """
    manager_level = config.ROLE_HIERARCHY.get(manager_role, 0)
    target_level = config.ROLE_HIERARCHY.get(target_role, 0)
    
    # Не можна керувати собою та вищими
    if target_level >= manager_level:
        return False
    
    # Спеціальні правила
    if manager_role == 'owner':
        return True  # Власник може все
    
    if manager_role == 'superadmin':
        return target_role in ['admin', 'mentor', 'guest']
    
    if manager_role == 'admin':
        return target_role in ['mentor', 'guest']
    
    return False


def get_user_role(db, telegram_id):
    """
    Отримує роль користувача з бази даних.
    
    Returns:
        str: роль користувача або None якщо не знайдено
    """
    user = db.get_user_by_telegram_id(telegram_id)
    return user['role'] if user else None


def has_role_level(user_role, required_role):
    """
    Перевіряє чи має користувач достатній рівень ролі.
    
    Args:
        user_role: поточна роль користувача
        required_role: необхідна мінімальна роль
    
    Returns:
        bool: True якщо рівень достатній
    """
    user_level = config.ROLE_HIERARCHY.get(user_role, 0)
    required_level = config.ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level
