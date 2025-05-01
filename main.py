
from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests

# Flask-сервер
app = Flask(__name__)

@app.route("/")
def home():
    return "I'm alive"

@app.route("/frontend/")
def serve_frontend():
    return send_from_directory("static", "index.html")

@app.route("/frontend/<path:path>")
def serve_static_file(path):
    return send_from_directory("static", path)

# Telegram-бот
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = "https://" + os.getenv("REPL_SLUG", "") + "." + os.getenv("REPL_OWNER", "") + ".repl.co/frontend/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Открыть чат с ИИ", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await update.message.reply_text("Добро пожаловать! Нажми кнопку ниже, чтобы запустить ИИ:", reply_markup=keyboard)

app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))

# Запуск Telegram-бота и Flask-сервера
import threading

def run_telegram():
    app_telegram.run_polling()

def run_flask():
    app.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    threading.Thread(target=run_telegram).start()
    run_flask()
