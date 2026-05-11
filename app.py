import os
import requests
from flask import Flask, request
from telegram import Bot, Update

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    update = Update.de_json(req, bot)
    chat_id = update.effective_chat.id
    text = update.message.text if update.message else ""

    if text == "/start":
        send_message(chat_id, "မင်္ဂလာပါ။ Echo Bot ပါ။ တစ်ခုခုရိုက်ကြည့်ပါ။")
    elif text:
        # AI မပါဘူး။ ပြန်ထပ်ဖြေမယ်
        send_message(chat_id, f"ခင်ဗျားပြောတာ: {text}")
    
    return "ok"

@app.route("/")
def home():
    return "Echo Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
