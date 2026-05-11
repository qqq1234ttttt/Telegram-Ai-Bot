import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from huggingface_hub import InferenceClient

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY") # Token ကို Read ခွင့်နဲ့ ပြန်လုပ်ဖို့ မမေ့ပါနဲ့

bot = Bot(token=TELEGRAM_TOKEN)
# ✅ Open-access model အတွက် provider ကို "hf-inference" ပြန်သုံးပါ
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)
user_conversations = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
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
        send_message(chat_id, "မင်္ဂလာပါ။ TinyLlama AI Bot ပါ။")
    elif text == "/clear":
        user_conversations[user_id] = []
        send_message(chat_id, "မှတ်ဉာဏ်ရှင်းပြီးပါပြီ။")
    elif text:
        send_message(chat_id, "စဉ်းစားနေပါတယ်...")
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        user_conversations[user_id].append({"role": "user", "content": text})
        try:
            # ✅ သေချာအလုပ်ဖြစ်မယ့် Open-access Model
            completion = client.chat.completions.create(
                model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                messages=user_conversations[user_id],
                max_tokens=300,
                temperature=0.7,
            )
            reply = completion.choices[0].message["content"]
            user_conversations[user_id].append({"role": "assistant", "content": reply})
            send_message(chat_id, reply[:4000])
        except Exception as e:
            print(f"AI Error: {e}")
            send_message(chat_id, f"AI အမှား: {str(e)}")
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
