import os
import logging
import requests
import json
import sys
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем токен
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def test_bot():
    if not BOT_TOKEN:
        logger.error("❌ Токен бота отсутствует в переменных окружения")
        return False
        
    logger.info(f"✅ Получен токен бота: {BOT_TOKEN[:6]}...{BOT_TOKEN[-4:]}")
    
    # Проверяем формат токена
    if ":" not in BOT_TOKEN:
        logger.error("❌ Токен имеет неверный формат (отсутствует двоеточие)")
        return False
    
    # Делаем простой GET-запрос к API Telegram для получения информации о боте
    try:
        logger.info("🔍 Выполняем запрос к API Telegram...")
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(api_url, timeout=10)
        
        logger.info(f"✅ Получен ответ от API Telegram, статус: {response.status_code}")
        
        if response.status_code == 200:
            # Парсим JSON-ответ
            bot_info = response.json()
            logger.info(f"✅ Информация о боте: {json.dumps(bot_info, indent=2)}")
            
            if bot_info.get("ok") and bot_info.get("result"):
                logger.info(f"✅ Бот успешно найден: @{bot_info['result'].get('username')} (ID: {bot_info['result'].get('id')})")
                return True
            else:
                logger.error(f"❌ Ошибка в данных бота: {bot_info}")
                return False
        else:
            logger.error(f"❌ Ошибка API: {response.status_code}")
            logger.error(f"❌ Текст ответа: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обращении к API Telegram: {str(e)}")
        return False

# Запускаем тест
if __name__ == "__main__":
    logger.info("🚀 Запуск теста Telegram бота...")
    result = asyncio.run(test_bot())
    
    if result:
        logger.info("🎉 Тест успешно пройден! Бот работает корректно.")
        sys.exit(0)
    else:
        logger.error("⛔ Тест не пройден. Бот не работает.")
        sys.exit(1)