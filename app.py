import os
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Бот работает! Твой HYDRA на связи.")

@bot.message_handler(func=lambda m: True)
def echo(m):
    bot.reply_to(m, f"Ты написал: {m.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '!', 200
    return 'Bad request', 403

@app.route('/')
def index():
    return 'Bot is running'

if __name__ == '__main__':
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/webhook")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
