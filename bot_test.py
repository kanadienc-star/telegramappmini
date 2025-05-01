#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, ApplicationBuilder

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение токена бота из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)

# Определение обработчиков команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил команду /start")
    
    await update.message.reply_text(f"👋 Привет, {user.first_name}! Это тестовый бот для проверки работы Telegram API.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /test"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил команду /test")
    
    await update.message.reply_text("✅ Тестовая команда работает!")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /info - показывает информацию о токене и окружении"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил команду /info")
    
    # Информация о боте
    me = await context.bot.get_me()
    bot_info = (
        f"📊 *Информация о боте*\n\n"
        f"ID бота: `{me.id}`\n"
        f"Имя: {me.first_name}\n"
        f"Юзернейм: @{me.username}\n"
        f"Токен: `{BOT_TOKEN[:8]}...`\n\n"
        f"🔄 *Окружение Replit*\n"
        f"REPL_ID: `{os.getenv('REPL_ID', 'Не задан')}`\n"
        f"REPL_SLUG: `{os.getenv('REPL_SLUG', 'Не задан')}`\n"
        f"REPL_OWNER: `{os.getenv('REPL_OWNER', 'Не задан')}`\n"
    )
    
    await update.message.reply_text(bot_info, parse_mode="Markdown")

async def main():
    """Основная функция для запуска бота"""
    try:
        logger.info(f"🚀 Запуск тестового бота с токеном {BOT_TOKEN[:8]}...")
        
        # Создание приложения с правильной инициализацией
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.info("✅ Приложение создано")
        
        # Добавление обработчиков команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(CommandHandler("info", info_command))
        logger.info("✅ Обработчики команд добавлены")
        
        # Настройка меню команд
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Запустить бота"),
            BotCommand("test", "Проверить работу бота"),
            BotCommand("info", "Информация о боте и окружении")
        ]
        
        await application.bot.set_my_commands(commands)
        logger.info("✅ Меню команд настроено")
        
        # Получение информации о боте
        me = await application.bot.get_me()
        logger.info(f"✅ Бот @{me.username} (ID: {me.id}) успешно подключен к API")
        
        # Запуск бота в режиме long polling
        logger.info("📡 Запуск получения обновлений...")
        
        # Правильный способ запуска бота в новой версии PTB
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=["message", "callback_query"])
        logger.info("✅ Бот успешно запущен и ожидает команды!")
        
        # Держим бота запущенным до сигнала остановки
        # Чтобы остановить выполнение скрипта, нажмите Ctrl+C
        try:
            await asyncio.sleep(120)  # Ждем 2 минуты, после чего завершаем работу
            logger.info("⏱️ Завершаем тест бота через 2 минуты")
        except asyncio.CancelledError:
            pass
            
        # Корректное завершение работы
        logger.info("🛑 Остановка бота...")
        await application.updater.stop()
        await application.stop()
        logger.info("✅ Бот успешно остановлен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("🔍 Запуск проверки Telegram бота...")
    asyncio.run(main())