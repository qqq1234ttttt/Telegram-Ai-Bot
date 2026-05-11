import os
import json
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from huggingface_hub import InferenceClient

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)

# သုံးစွဲသူ conversation memory
user_conversations = {}

# ---------- Command handlers ----------
def handle_start(chat_id):
    asyncio.create_task(bot.send_message(chat_id=chat_id, text="မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။"))

def handle_help(chat_id):
    asyncio.create_task(bot.send_message(chat_id=chat_id, text="/start - စတင်ရန်\n/clear - မှတ်ဉာဏ်ရှင်းရန်"))

def handle_clear(chat_id, user_id):
    user_conversations[user_id] = []
    asyncio.create_task(bot.send_message(chat_id=chat_id, text="စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။"))

def handle_ai(chat_id, user_id, text):
    # Conversation memory ထဲထည့်
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append({"role": "user", "content": text})
    
    try:
        # Hugging Face API ခေါ်ပါ (synchronous, ဒါပေမယ့် thread ထဲထည့်စရာမလို၊ ခဏလောက်ကြာနိုင်)
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
        asyncio.create_task(bot.send_message(chat_id=chat_id, text=reply))
    except Exception as e:
        print(f"AI error: {e}")
        asyncio.create_task(bot.send_message(chat_id=chat_id, text="AI ခေါ်ရာမှာ အမှားဖြစ်သွားပါတယ်။ ခဏကြာမှ ပြန်စမ်းပါ။"))

# ---------- Webhook endpoint ----------
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    update = Update.de_json(req, bot)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text if update.message else None
    
    if not message_text:
        return "ok"
    
    # Command detection
    if message_text.startswith("/start"):
        handle_start(chat_id)
    elif message_text.startswith("/help"):
        handle_help(chat_id)
    elif message_text.startswith("/clear"):
        handle_clear(chat_id, user_id)
    else:
        # AI အဖြေ (command မဟုတ်တဲ့စာ)
        handle_ai(chat_id, user_id, message_text)
    
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

@app.route("/set_webhook")
def set_webhook():
    # Render ရဲ့ public URL ကို ယူမယ်
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not external_url:
        return "RENDER_EXTERNAL_URL not set", 500
    webhook_url = f"{external_url}/{TELEGRAM_TOKEN}"
    import requests
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", json={"url": webhook_url})
    return r.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
