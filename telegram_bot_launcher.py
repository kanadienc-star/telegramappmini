#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Отдельный скрипт для запуска Telegram бота, который используется для команды `python telegram_bot_launcher.py`.
Это позволяет запускать Telegram бота отдельно от основного Flask-приложения.
"""

import asyncio
import os
import sys
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, ApplicationBuilder, MessageHandler, filters

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

# Получение URL для Telegram WebApp
REPL_SLUG = os.getenv("REPL_SLUG", "")
REPL_OWNER = os.getenv("REPL_OWNER", "")
REPL_ID = os.getenv("REPL_ID", "")

if REPL_SLUG and REPL_OWNER:
    # Версия с названием проекта
    WEBAPP_URL = f"https://{REPL_SLUG}.{REPL_OWNER}.repl.co/frontend/"
elif REPL_ID:
    # Версия с ID проекта
    WEBAPP_URL = f"https://{REPL_ID}.id.repl.co/frontend/"
else:
    # Локальная версия для тестирования, если мы не на Replit
    WEBAPP_URL = "http://localhost:5000/frontend/"

logger.info(f"WebApp URL настроен: {WEBAPP_URL}")

# Обработчики команд бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил команду /start")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Открыть чат с ИИ", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await update.message.reply_html(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"Я бот с искусственным интеллектом, который всегда отвечает на русском языке.\n\n"
        f"Нажмите на кнопку ниже, чтобы открыть чат и начать общение со мной:",
        reply_markup=keyboard
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил команду /help")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Открыть чат с ИИ", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await update.message.reply_text(
        "🤖 *Помощь по командам*\n\n"
        "*/start* - Начать работу с ботом и открыть чат\n"
        "*/help* - Показать это сообщение помощи\n"
        "*/about* - Информация о боте и его возможностях\n\n"
        "Вы также можете напрямую использовать кнопку ниже, чтобы открыть чат:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /about"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил команду /about")
    
    await update.message.reply_text(
        "🤖 *О боте*\n\n"
        "Я ИИ-ассистент на базе модели Meta-Llama-3-8B-Instruct, который всегда отвечает на русском языке.\n\n"
        "Вы можете задать мне любые вопросы, и я постараюсь дать на них информативные ответы. "
        "Я могу помочь с объяснением сложных тем, написанием текстов, советами и многим другим.\n\n"
        "*Команды:*\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать помощь\n"
        "/about - О боте\n\n"
        "Разработано в Replit",
        parse_mode="Markdown"
    )

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для обычных текстовых сообщений"""
    user = update.effective_user
    message_text = update.message.text
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без юзернейма'}) отправил текстовое сообщение: {message_text[:20]}...")
    
    # Отправляем пользователю сообщение с инструкцией
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Открыть чат с ИИ", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await update.message.reply_text(
        "Чтобы начать общение с ИИ, пожалуйста, используйте кнопку ниже:",
        reply_markup=keyboard
    )

async def main():
    """Основная функция для запуска бота"""
    try:
        logger.info(f"🚀 Запуск бота с токеном {BOT_TOKEN[:8]}...")
        
        # Создание приложения
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.info("✅ Приложение создано")
        
        # Добавление обработчиков команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
        logger.info("✅ Обработчики команд добавлены")
        
        # Обработчик ошибок
        async def error_handler(update, context):
            logger.error(f"❌ Ошибка при обработке обновления: {context.error}")
            try:
                if update and update.effective_user:
                    logger.error(f"Ошибка произошла при обработке запроса от пользователя {update.effective_user.id}")
            except:
                pass
        
        application.add_error_handler(error_handler)
        logger.info("✅ Обработчик ошибок добавлен")
        
        # Настройка меню команд
        from telegram import BotCommand
        commands = [
            BotCommand("start", "🚀 Начать работу с ботом"),
            BotCommand("help", "❓ Показать помощь"),
            BotCommand("about", "ℹ️ О боте")
        ]
        
        await application.bot.set_my_commands(commands)
        logger.info("✅ Меню команд настроено")
        
        # Получение информации о боте
        me = await application.bot.get_me()
        logger.info(f"✅ Бот @{me.username} (ID: {me.id}) успешно подключен к API")
        
        # Запуск бота
        logger.info("📡 Запуск получения обновлений...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=["message", "callback_query"])
        logger.info("✅ Бот успешно запущен и ожидает команды!")
        
        # Держим бота запущенным до сигнала остановки
        # Чтобы остановить выполнение скрипта, нажмите Ctrl+C
        while True:
            await asyncio.sleep(3600)  # Проверяем каждый час
            logger.info("✓ Бот продолжает работать...")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("🔍 Запуск Telegram бота в отдельном процессе...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения работы, останавливаем бота...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())