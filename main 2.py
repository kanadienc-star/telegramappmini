from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests
import logging

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

# ВАЖНО: используем фиксированный URL, так как он гарантированно работает
WEBAPP_URL = "https://izhelokov.replit.app/frontend/"
logger.info(f"WebApp URL настроен: {WEBAPP_URL}")

# Проверка доступности через DNS
import socket
try:
    socket_info = socket.getaddrinfo("izhelokov.replit.app", 443)
    logger.info(f"Проверка URL успешна: {socket_info[0][4][0]}")
except Exception as e:
    logger.error(f"Не удалось разрешить DNS для izhelokov.replit.app: {str(e)}")

logger.info(f"WebApp URL настроен: {WEBAPP_URL}")

if not DEEPINFRA_API_KEY:
    logger.warning("DEEPINFRA_API_KEY не найден в переменных окружения")
if not BOT_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

# Flask-сервер
app = Flask(__name__)

# Добавляем кеширование и CORS-заголовки для запросов
@app.after_request
def add_header(response):
    # Кеширование
    response.cache_control.max_age = 300  # кэшировать 5 минут
    
    # CORS-заголовки для работы в Telegram WebApp
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response

@app.route("/")
def home():
    # Теперь корневая страница показывает то же самое, что и /frontend/
    logger.info("Запрос к корневому URL. User-Agent: " + request.headers.get('User-Agent', '')[:50])
    return send_from_directory("static", "index.html")

@app.route("/frontend/")
def serve_frontend():
    return send_from_directory("static", "index.html")

@app.route("/frontend/<path:path>")
def serve_static_file(path):
    return send_from_directory("static", path)
    
# Специальный маршрут для index.html - нужен для WebApp
@app.route("/index.html")
def serve_index_html():
    logger.info("Запрос к /index.html")
    return send_from_directory("static", "index.html")
    
# Специальный маршрут для telegram - с редиректом на корневой URL
@app.route("/telegram")
def telegram_webapp_redirect():
    logger.info("Запрос от Telegram WebApp к /telegram - делаем редирект")
    from flask import redirect
    return redirect("/")
    
# Добавляем маршрут для корневых ресурсов, чтобы они были доступны и в корне сайта
@app.route("/<path:path>")
def root_static_files(path):
    # Проверяем расширение файла
    if '.' in path and not path.startswith('frontend/'):  # если это файл с расширением (css, js и т.д.)
        try:
            logger.info(f"Запрос к корневому ресурсу: /{path}")
            return send_from_directory("static", path)
        except Exception as e:
            logger.error(f"Ошибка при доступе к /{path}: {str(e)}")
            # Если файл не найден в static, продолжаем выполнение следующих маршрутов
            pass
    # Для URL, начинающихся с /telegram, также возвращаем основной интерфейс
    # Это может быть необходимо для Telegram WebApp
    if path.startswith('telegram'):
        logger.info(f"Запрос от Telegram WebApp: /{path}")
        return send_from_directory("static", "index.html")

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    try:
        logger.info(f"Получен запрос на /chat")
        logger.info(f"Метод запроса: {request.method}")
        
        # Обработка OPTIONS запроса для CORS
        if request.method == "OPTIONS":
            return "", 200
            
        logger.info(f"Content-Type: {request.headers.get('Content-Type')}")
        logger.info(f"Тело запроса: {request.get_data(as_text=True)}")
        
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
        
        logger.info(f"Используемая модель: {request_data['model']}")
        
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
            logger.info(f"Структура ответа API: {str(response_json.keys())}")
            
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
        
        # Проверка наличия ответа от API
        if 'response' in locals() and hasattr(response, 'status_code'):
            logger.error(f"Код ответа API: {response.status_code}")
            if hasattr(response, 'text'):
                logger.error(f"Текст ответа API: {response.text[:500]}")
        
        # Запасные ответы на случай проблем с API
        fallback_responses = [
            "Извините, я не могу сейчас сформулировать хороший ответ. Можете задать вопрос иначе?",
            "В данный момент у меня проблемы с доступом к базе знаний. Пожалуйста, попробуйте позже.",
            "Интересный вопрос! К сожалению, сейчас я не могу дать на него полноценный ответ.",
            "Извините за неудобство, но в данный момент я не могу ответить на этот вопрос."
        ]
        import random
        return jsonify({'reply': random.choice(fallback_responses)})

# Telegram-бот - команды и обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без имени'}) отправил команду /start")
    
    # Вместо WebApp используем обычную ссылку - иногда это работает лучше
    url = "https://izhelokov.replit.app"
    logger.info(f"Задаем обычный URL: {url}")
    
    # Формируем клавиатуру с ОБЫЧНОЙ кнопкой-ссылкой
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Открыть чат с ИИ в браузере", url=url)]
    ])
    
    logger.info(f"Отправляем сообщение с обычной кнопкой-ссылкой пользователю {user.id}")
    
    await update.message.reply_html(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"Я бот с искусственным интеллектом, который всегда отвечает на русском языке.\n\n"
        f"Нажмите на кнопку ниже, чтобы открыть чат и начать общение со мной:",
        reply_markup=keyboard
    )
    
    logger.info(f"Сообщение отправлено пользователю {user.id}")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username}) отправил команду /about")
    
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

# Запуск Telegram-бота и Flask-сервера
import threading

import asyncio

async def run_telegram_async():
    """Асинхронная функция для запуска Telegram-бота"""
    try:
        logger.info("🤖 Инициализация Telegram бота...")
        
        if not BOT_TOKEN:
            logger.error("❌ Невозможно запустить Telegram бота - отсутствует токен")
            return

        logger.info(f"✅ Токен Telegram бота получен: {BOT_TOKEN[:8]}***")
        logger.info(f"✅ URL для WebApp настроен: {WEBAPP_URL}")
        
        # Проверка валидности токена бота
        if not BOT_TOKEN.strip():
            logger.error("❌ Токен бота пустой или содержит только пробелы")
            return
            
        if ":" not in BOT_TOKEN:
            logger.error("❌ Токен бота имеет неверный формат (отсутствует двоеточие)")
            return
        
        try:
            # Настраиваем обработчик команды help
            async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    user = update.effective_user
                    logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без имени'}) отправил команду /help")
                    
                    # Используем обычный URL вместо WebApp
                    url = "https://izhelokov.replit.app/"
                    logger.info(f"Задаем URL для help: {url}")
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✨ Открыть чат с ИИ в браузере", url=url)]
                    ])
                    
                    logger.info(f"Отправляем сообщение помощи пользователю {user.id}")
                    
                    await update.message.reply_text(
                        "🤖 *Помощь по командам*\n\n"
                        "*/start* - Начать работу с ботом и открыть чат\n"
                        "*/help* - Показать это сообщение помощи\n"
                        "*/about* - Информация о боте и его возможностях\n\n"
                        "Вы также можете напрямую использовать кнопку ниже, чтобы открыть чат:",
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    logger.info(f"✅ Команда /help успешно обработана для {user.id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке команды /help: {str(e)}")
            
            # Создаем объект бота с расширенным логированием запросов
            logger.info("Создание объекта ApplicationBuilder...")
            app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
            logger.info("✅ ApplicationBuilder создан успешно")
            
            # Устанавливаем команды бота для меню
            bot_commands = [
                ("start", "🚀 Начать работу с ботом"),
                ("help", "❓ Показать помощь"),
                ("about", "ℹ️ О боте")
            ]
            
            # Регистрируем все обработчики команд
            logger.info("Регистрация обработчиков команд...")
            app_telegram.add_handler(CommandHandler("start", start))
            app_telegram.add_handler(CommandHandler("help", help_command))
            app_telegram.add_handler(CommandHandler("about", about_command))
            logger.info("✅ Все обработчики команд зарегистрированы")
            
            # Обработчик для любых текстовых сообщений, не являющихся командами
            from telegram.ext import MessageHandler, filters
            
            async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user = update.effective_user
                message_text = update.message.text
                logger.info(f"Пользователь {user.id} (@{user.username if user.username else 'без имени'}) отправил текстовое сообщение: {message_text[:20]}...")
                
                # Используем обычный URL вместо WebApp
                url = "https://izhelokov.replit.app/"
                logger.info(f"Задаем URL для сообщения: {url}")
                
                # Отправляем пользователю сообщение с инструкцией
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✨ Открыть чат с ИИ в браузере", url=url)]
                ])
                
                logger.info(f"Отправляем ответное сообщение пользователю {user.id}")
                
                await update.message.reply_text(
                    "Чтобы начать общение с ИИ, пожалуйста, используйте кнопку ниже:",
                    reply_markup=keyboard
                )
                
                logger.info(f"Ответное сообщение отправлено пользователю {user.id}")
            
            # Добавляем обработчик обычных текстовых сообщений
            app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
            logger.info("✅ Обработчик текстовых сообщений добавлен")
            
            # Обработчик ошибок для логирования неожиданных проблем
            async def error_handler(update, context):
                logger.error(f"❌ Ошибка при обработке обновления: {context.error}")
                try:
                    if update and update.effective_user:
                        logger.error(f"Ошибка произошла при обработке запроса от пользователя {update.effective_user.id}")
                except:
                    pass
            
            app_telegram.add_error_handler(error_handler)
            logger.info("✅ Обработчик ошибок добавлен")
            
            # Установим команды в меню бота
            from telegram.ext import Application
            async def setup_bot_commands():
                try:
                    from telegram import BotCommand
                    await app_telegram.bot.set_my_commands([BotCommand(command, description) for command, description in bot_commands])
                    logger.info("✅ Команды бота успешно настроены в меню")
                except Exception as e:
                    logger.error(f"❌ Ошибка при настройке команд бота: {str(e)}")
                    
            # Запускаем настройку команд бота
            app_telegram.create_task(setup_bot_commands())
            
            logger.info("✅ Telegram бот успешно настроен, запускаем polling...")
            
            # Попытка отправить тестовое сообщение самому себе для проверки соединения
            async def self_test():
                try:
                    me = await app_telegram.bot.get_me()
                    logger.info(f"✅ Соединение установлено успешно. Информация о боте: @{me.username} (ID: {me.id})")
                except Exception as e:
                    logger.error(f"❌ Ошибка при попытке получить информацию о боте: {str(e)}")
            
            app_telegram.create_task(self_test())
            
            # Правильная последовательность запуска бота в новой версии PTB
            logger.info("🔄 Инициализируем приложение бота...")
            await app_telegram.initialize()
            logger.info("🔄 Запускаем приложение бота...")
            await app_telegram.start()
            logger.info("🔄 Запускаем получение обновлений...")
            await app_telegram.updater.start_polling(allowed_updates=["message", "callback_query"])
            logger.info("✅ Telegram бот успешно запущен!")
            
            # Держим бота запущенным
            while True:
                await asyncio.sleep(1000)  # Бесконечный цикл, чтобы бот работал постоянно
            
        except Exception as inner_e:
            logger.error(f"❌ Внутренняя ошибка при настройке бота: {str(inner_e)}")
            import traceback
            logger.error(traceback.format_exc())
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске Telegram бота: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def run_telegram():
    """Запускает асинхронный Telegram-бот в отдельном потоке с полным логированием и обработкой ошибок"""
    try:
        logger.info("🚀 Запуск асинхронного Telegram бота...")
        
        # Создаем и запускаем event loop для асинхронного бота
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем асинхронную функцию в этом event loop
        loop.run_until_complete(run_telegram_async())
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске асинхронного Telegram бота: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def run_flask():
    logger.info("Запуск Flask сервера...")
    app.run(host="0.0.0.0", port=5000)

# Автоматически запускаем Telegram бота при импорте этого модуля (для Gunicorn)
# Это позволит боту работать автоматически при запуске через Gunicorn
try:
    # Запускаем Telegram бота в новом потоке
    telegram_thread = threading.Thread(target=run_telegram, name="TelegramBotThread")
    telegram_thread.daemon = True  # Поток будет автоматически завершен при завершении основного
    logger.info("🤖 Автоматический запуск телеграм-бота при старте приложения...")
    telegram_thread.start()
    logger.info("✅ Telegram бот запущен в фоновом режиме")
except Exception as e:
    logger.error(f"❌ Ошибка автоматического запуска Telegram бота: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Запускаем Flask в основном потоке, если скрипт запущен напрямую
    logger.info("🚀 Запуск приложения в режиме разработки...")
    try:
        # Запускаем Flask в основном потоке
        logger.info("✅ Запускаем Flask в основном потоке")
        run_flask()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске Flask: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())