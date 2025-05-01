from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Замените на токен своего бота
BOT_TOKEN = "твой_токен"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # После развертывания на Replit вы получите постоянную ссылку
    # Формат: https://имяпроекта.username.repl.co
    # Замените на вашу постоянную ссылку после развертывания
    permanent_url = "https://ваш-постоянный-домен.repl.co"
    
    keyboard = [
        [InlineKeyboardButton("Открыть чат с ИИ", web_app=WebAppInfo(url=permanent_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Нажми кнопку ниже, чтобы запустить чат с ИИ:", reply_markup=reply_markup)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()