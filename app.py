import os
import json
import requests
from flask import Flask, request
from telegram import Bot, Update
from huggingface_hub import InferenceClient

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)
user_conversations = {}

def send_message(chat_id, text):
    """Telegram message ပို့ရန် helper function"""
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
    user_id = update.effective_user.id
    text = update.message.text if update.message else ""

    if text == "/start":
        send_message(chat_id, "မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။")
    elif text == "/help":
        send_message(chat_id, "/start - စတင်ရန်\n/clear - မှတ်ဉာဏ်ရှင်းရန်")
    elif text == "/clear":
        user_conversations[user_id] = []
        send_message(chat_id, "စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။")
    elif text:
        # AI မေးခွန်း
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        user_conversations[user_id].append({"role": "user", "content": text})
        try:
            completion = client.chat.completions.create(
                model="microsoft/Phi-3-mini-4k-instruct",
                messages=user_conversations[user_id],
                max_tokens=500,
                temperature=0.7,
            )
            reply = completion.choices[0].message["content"]
            user_conversations[user_id].append({"role": "assistant", "content": reply})
            if len(reply) > 4000:
                reply = reply[:4000] + "..."
            send_message(chat_id, reply)
        except Exception as e:
            print(f"AI error: {e}")
            send_message(chat_id, "AI ခေါ်ရာမှာ အမှားဖြစ်သွားပါတယ်။ ခဏကြာမှ ပြန်စမ်းပါ။")
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

@app.route("/set_webhook")
def set_webhook():
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not external_url:
        return "RENDER_EXTERNAL_URL not set", 500
    webhook_url = f"{external_url}/{TELEGRAM_TOKEN}"
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", json={"url": webhook_url})
    return r.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
