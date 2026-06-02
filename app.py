import os
import logging
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            logger.info(f"Получен запрос: {json_string[:200]}")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '!', 200
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            return 'Error', 500
    return 'Bad request', 403

@app.route('/')
def index():
    return 'Bot is running'

@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Обработчик /start вызван")
    bot.reply_to(message, "✅ Бот работает! Связь есть!")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    logger.info(f"Получено сообщение: {message.text}")
    bot.reply_to(message, f"Ты написал: {message.text}")

if __name__ == '__main__':
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/webhook")
        logger.info(f"Вебхук установлен на {RENDER_URL}/webhook")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
