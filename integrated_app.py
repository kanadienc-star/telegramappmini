#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Интегрированный запуск веб-приложения и Telegram бота в одном процессе.
Это решение лучше подходит для платформы Replit, где нежелательно запускать несколько процессов.
"""

import os
import logging
import threading
import asyncio
import requests
from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение ключей API
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Получение URL для Telegram WebApp
REPL_SLUG = os.getenv("REPL_SLUG", "")
REPL_OWNER = os.getenv("REPL_OWNER", "")
REPL_ID = os.getenv("REPL_ID", "")

# Используем более надежный URL для Telegram WebApp
# ВАЖНО: используем фиксированный URL, так как он работает (не меняйте его)
WEBAPP_URL = "https://izhelokov.replit.app/frontend/"
logger.info(f"Используем фиксированный URL для WebApp: {WEBAPP_URL}")

# Проверяем доступность через DNS и Socket API
import socket
try:
    socket_info = socket.getaddrinfo("izhelokov.replit.app", 443)
    logger.info(f"Проверка URL успешна: {socket_info[0][4][0]}")
except Exception as e:
    logger.error(f"Ошибка при проверке URL через DNS: {str(e)}")

# Для диагностики добавим информацию о резервных URL
logger.info(f"Резервные URL конфигурации:")
if REPL_OWNER:
    logger.info(f"- REPL_OWNER URL: https://{REPL_OWNER}.replit.app/frontend/")
if REPL_SLUG and REPL_OWNER:
    logger.info(f"- REPL_SLUG URL: https://{REPL_SLUG}.{REPL_OWNER}.repl.co/frontend/")
if REPL_ID:
    logger.info(f"- REPL_ID URL: https://{REPL_ID}.id.repl.co/frontend/")

logger.info(f"WebApp URL настроен: {WEBAPP_URL}")

# Flask-сервер
app = Flask(__name__)

# Добавляем кеширование для статических файлов
@app.after_request
def add_header(response):
    response.cache_control.max_age = 300  # кэшировать 5 минут
    return response

@app.route("/")
def home():
    # Редирект с корневой страницы на интерфейс чата
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0;url=/frontend/">
        <title>Переадресация на чат</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: #f5f5f5;
            }
            a {
                color: #0077cc;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <h1>Переадресация на интерфейс чата...</h1>
        <p>Если вы не были перенаправлены автоматически, <a href="/frontend/">нажмите здесь</a>.</p>
    </body>
    </html>
    """

# Повышаем уровень логирования для URL маршрутов
import os
from pathlib import Path
import logging

# Проверяем, существуют ли каталоги
logger.info(f"Проверка каталога frontend/: {os.path.exists('frontend')}")
logger.info(f"Проверка каталога static/: {os.path.exists('static')}")

if os.path.exists('frontend'):
    logger.info(f"Содержимое frontend/: {os.listdir('frontend')}")
if os.path.exists('static'):
    logger.info(f"Содержимое static/: {os.listdir('static')}")

# Добавляем дополнительные маршруты для обслуживания статики
@app.route("/frontend")
def redirect_frontend():
    """Редирект с /frontend на /frontend/ (с слешем)"""
    logger.info("Получен запрос без слеша на /frontend, выполняем редирект")
    # app.redirect_to не работает в некоторых версиях Flask
    return app.redirect("/frontend/")

@app.route("/frontend/", methods=["GET", "HEAD", "OPTIONS"])
def serve_frontend():
    """
    Обслуживает основной HTML-файл чата.
    Прверяет наличие файла в каталоге frontend/, если там нет - берет из static/
    """
    logger.info(f"Получен запрос на /frontend/ метода {request.method}")
    
    # Обрабатываем OPTIONS запрос для CORS
    if request.method == "OPTIONS":
        logger.info("Обрабатываем OPTIONS запрос")
        return "", 200
        
    try:
        # Сначала пробуем найти файл в каталоге frontend/
        frontend_path = Path('frontend/index.html')
        logger.info(f"Проверяем наличие файла {frontend_path}, существует: {frontend_path.exists()}")
        
        if frontend_path.exists():
            logger.info("Возвращаем файл из frontend/index.html")
            return send_from_directory("frontend", "index.html")
        else:
            # Если не найден, используем файл из static/
            static_path = Path('static/index.html')
            logger.info(f"Файл в frontend/ не найден, проверяем {static_path}, существует: {static_path.exists()}")
            
            if static_path.exists():
                logger.info("Возвращаем файл из static/index.html")
                return send_from_directory("static", "index.html")
            else:
                logger.error("HTML файл не найден ни в frontend/, ни в static/")
                return "Ошибка: HTML файл не найден", 404
    except Exception as e:
        logger.error(f"Ошибка при обслуживании frontend/: {str(e)}")
        # В случае ошибки, возвращаем базовую HTML страницу
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ИИ Чат</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <h1>Ошибка при загрузке интерфейса</h1>
            <p>Произошла ошибка при загрузке интерфейса. Пожалуйста, попробуйте позже.</p>
            <p>Технические детали ошибки: {}</p>
        </body>
        </html>
        """.format(str(e)), 500

@app.route("/frontend/<path:path>", methods=["GET", "HEAD", "OPTIONS"])
def serve_static_file(path):
    """
    Обслуживает статические файлы из frontend/ или static/
    """
    logger.info(f"Получен запрос на /frontend/{path}")
    
    # Обрабатываем OPTIONS запрос для CORS
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        # Сначала пробуем найти в frontend/
        frontend_path = os.path.join("frontend", path)
        if os.path.exists(frontend_path):
            logger.info(f"Возвращаем файл из frontend/{path}")
            return send_from_directory("frontend", path)
        else:
            # Если не найдено - берем из static/
            static_path = os.path.join("static", path)
            if os.path.exists(static_path):
                logger.info(f"Возвращаем файл из static/{path}")
                return send_from_directory("static", path)
            else:
                logger.error(f"Файл {path} не найден ни в frontend/, ни в static/")
                return f"Ошибка: файл {path} не найден", 404
    except Exception as e:
        logger.error(f"Ошибка при обслуживании static файла {path}: {str(e)}")
        return f"Ошибка: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        if not request.is_json:
            logger.error("Запрос не содержит JSON")
            return jsonify({"reply": "Ошибка: ожидался JSON-запрос"}), 400
        
        user_input = request.json.get('message', '')
        logger.info(f"Получен запрос с сообщением: {user_input[:50]}...")
        
        # Формируем данные для запроса
        request_data = {
            "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "messages": [
                {"role": "system", "content": "Ты дружелюбный и умный помощник, который ОБЯЗАТЕЛЬНО отвечает на вопросы пользователя ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. " +
                                   "ВСЕГДА пиши свои ответы ТОЛЬКО НА РУССКОМ ЯЗЫКЕ, независимо от языка вопроса. " +
                                   "Стремись давать точные, информативные и полезные ответы. " +
                                   "Если не знаешь ответа, честно признайся в этом, но всё равно пиши на русском. " +
                                   "НИКОГДА не отвечай на английском или любом другом языке, кроме русского."},
                {"role": "user", "content": user_input + "\n\nОтветь мне обязательно на русском языке."}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        headers = {
            "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Логируем данные запроса
        if DEEPINFRA_API_KEY:
            logger.info(f"Отправка запроса на API DeepInfra с токеном: {DEEPINFRA_API_KEY[:5]}***")
        else:
            logger.error("DEEPINFRA_API_KEY не установлен или пустой!")
        
        # Делаем запрос к API
        response = requests.post(
            "https://api.deepinfra.com/v1/openai/chat/completions",
            headers=headers,
            json=request_data
        )
        
        # Проверяем статус ответа
        logger.info(f"Получен ответ от API со статусом: {response.status_code}")
        
        # Если статус не успешный, выдаем ошибку
        if response.status_code != 200:
            logger.error(f"Ошибка API: {response.status_code}")
            logger.error(f"Текст ответа: {response.text[:500]}")
            return jsonify({'reply': "Ошибка при получении ответа от API. Пожалуйста, попробуйте позже."}), 500
        
        # Парсим JSON-ответ
        try:
            response_json = response.json()
            
            # Проверяем структуру ответа
            if 'choices' not in response_json or not response_json['choices']:
                logger.error(f"Неверная структура ответа API: отсутствует 'choices'")
                return jsonify({'reply': "Получен неверный формат ответа от API. Пожалуйста, попробуйте позже."}), 500
                
            answer = response_json['choices'][0]['message']['content']
            
            # Ограничиваем длину ответа
            if len(answer) > 4000:
                answer = answer[:4000] + "..."
                
            logger.info(f"Получен ответ от API длиной {len(answer)} символов")
            return jsonify({'reply': answer})
        except Exception as e:
            logger.error(f"Ошибка при обработке JSON ответа: {str(e)}")
            logger.error(f"Исходный ответ: {response.text[:500]}")
            return jsonify({'reply': "Ошибка при обработке ответа. Пожалуйста, попробуйте позже."}), 500
    
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        
        # Запасные ответы на случай проблем с API
        fallback_responses = [
            "Извините, я не могу сейчас сформулировать хороший ответ. Можете задать вопрос иначе?",
            "В данный момент у меня проблемы с доступом к базе знаний. Пожалуйста, попробуйте позже.",
            "Интересный вопрос! К сожалению, сейчас я не могу дать на него полноценный ответ.",
            "Извините за неудобство, но в данный момент я не могу ответить на этот вопрос."
        ]
        import random
        return jsonify({'reply': random.choice(fallback_responses)})

# Флаг, который показывает, запущен ли уже бот
telegram_bot_started = False

# Telegram-бот - команды и обработчики
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

async def run_telegram_bot():
    """Асинхронная функция для запуска бота"""
    global telegram_bot_started
    
    if telegram_bot_started:
        logger.info("Бот уже запущен, пропускаем повторный запуск")
        return
        
    try:
        if not BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
            return
            
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
        
        # Устанавливаем флаг запуска бота
        telegram_bot_started = True
        
        # Держим бота запущенным до сигнала остановки
        while True:
            await asyncio.sleep(3600)  # Проверяем каждый час
            logger.info("✓ Бот продолжает работать...")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def start_telegram_bot_thread():
    """Запускает Telegram бота в отдельном потоке"""
    async def run_bot_wrapper():
        await run_telegram_bot()
        
    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_bot_wrapper())
        
    # Запуск в отдельном потоке
    bot_thread = threading.Thread(target=thread_target, daemon=True)
    bot_thread.start()
    logger.info("✅ Запущен поток для Telegram бота")
    return bot_thread

# При импорте этого модуля автоматически запускаем бот
# (когда gunicorn загружает приложение)
bot_thread = start_telegram_bot_thread()