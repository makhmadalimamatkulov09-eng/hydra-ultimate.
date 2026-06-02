import os
import sqlite3
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7103614975"))
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

app = Flask(__name__)

# ═══════════════════════════════════════════════
# САМОДИАГНОСТИКА
# ═══════════════════════════════════════════════
def run_diagnostics():
    results = []
    
    # 1. Токен
    if BOT_TOKEN and ":" in BOT_TOKEN and " " not in BOT_TOKEN:
        results.append("✅ Токен валиден")
    else:
        results.append("❌ Токен невалиден — проверь BOT_TOKEN")
    
    # 2. База данных
    try:
        conn = sqlite3.connect("/tmp/hydra_test.db")
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS diag (id INTEGER PRIMARY KEY, test TEXT)")
        cur.execute("INSERT INTO diag (test) VALUES ('diag')")
        conn.commit()
        cur.execute("SELECT test FROM diag LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0] == 'diag':
            results.append("✅ SQLite работает")
        else:
            results.append("❌ SQLite ошибка чтения")
    except Exception as e:
        results.append(f"❌ SQLite ошибка: {e}")
    
    # 3. Шифрование
    try:
        from cryptography.fernet import Fernet
        key = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key().decode())
        cipher = Fernet(key.encode())
        enc = cipher.encrypt(b"test")
        dec = cipher.decrypt(enc)
        if dec == b"test":
            results.append("✅ Шифрование работает")
        else:
            results.append("❌ Шифрование ошибка дешифровки")
    except Exception as e:
        results.append(f"❌ Шифрование ошибка: {e}")
    
    # 4. httpx
    try:
        import httpx
        results.append("✅ httpx импортирован")
    except Exception as e:
        results.append(f"❌ httpx ошибка: {e}")
    
    # 5. Pollinations API (исправленный формат)
    try:
        import requests
        r = requests.post("https://text.pollinations.ai/openai", 
                         json={"model": "openai", "messages": [{"role": "user", "content": "Say OK"}]}, 
                         headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
                         timeout=10)
        if r.status_code == 200:
            results.append("✅ Pollinations API доступен")
        else:
            results.append(f"❌ Pollinations статус {r.status_code}: {r.text[:100]}")
    except Exception as e:
        results.append(f"❌ Pollinations ошибка: {e}")
    
    # 6. Переменные окружения
    required = ["BOT_TOKEN", "ADMIN_ID", "ENCRYPTION_KEY", "RENDER_EXTERNAL_URL"]
    for var in required:
        if os.environ.get(var):
            results.append(f"✅ {var} задан")
        else:
            results.append(f"❌ {var} отсутствует")
    
    return "\n".join(results)

# Запускаем диагностику при старте
DIAG_RESULT = run_diagnostics()
print(f"[DIAGNOSTICS]\n{DIAG_RESULT}")

# Отправляем результат админу
try:
    bot.send_message(ADMIN_ID, f"🔍 Диагностика HYDRA:\n{DIAG_RESULT}")
except:
    pass

# ═══════════════════════════════════════════════
# КОМАНДЫ БОТА
# ═══════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ Бот работает! Диагностика пройдена.\n/diag — проверка\n/test_llm — тест LLM")

@bot.message_handler(commands=['diag'])
def diag(m):
    result = run_diagnostics()
    bot.reply_to(m, f"🔍 Результаты диагностики:\n{result}")

@bot.message_handler(commands=['test_llm'])
def test_llm(m):
    try:
        import requests
        prompt = m.text.replace('/test_llm', '').strip() or "Привет"
        r = requests.post("https://text.pollinations.ai/openai",
                         json={"model": "openai", "messages": [{"role": "user", "content": "[DAN] " + prompt}]},
                         headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
                         timeout=30)
        if r.status_code == 200:
            data = r.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа")
            bot.reply_to(m, f"🤖 LLM ответ:\n{text[:500]}")
        else:
            bot.reply_to(m, f"❌ Ошибка API: {r.status_code}\n{r.text[:200]}")
    except Exception as e:
        bot.reply_to(m, f"❌ Ошибка: {e}")

@bot.message_handler(func=lambda m: True)
def echo(m):
    bot.reply_to(m, f"Эхо: {m.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '!', 200
    return 'Bad request', 403

@app.route('/')
def index():
    return f"HYDRA Diag\n{DIAG_RESULT}"

if __name__ == '__main__':
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/webhook")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
