import os
import json
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from huggingface_hub import InferenceClient

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

# Bot Application ကို token နဲ့ တည်ဆောက်မယ် (v20+ ပုံစံ)
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Hugging Face client
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)
user_conversations = {}

# --- Command handlers (async ဖြစ်အောင်ရေးရမယ်) ---
async def start(update: Update, context):
    await update.message.reply_text("မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။")

async def help_cmd(update: Update, context):
    await update.message.reply_text("/start - စတင်ရန်\n/clear - မှတ်ဉာဏ်ရှင်းရန်")

async def clear(update: Update, context):
    uid = update.effective_chat.id
    user_conversations[uid] = []
    await update.message.reply_text("စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။")

async def ask_ai(update: Update, context):
    uid = update.effective_chat.id
    text = update.message.text
    if uid not in user_conversations:
        user_conversations[uid] = []
    user_conversations[uid].append({"role": "user", "content": text})
    try:
        completion = client.chat.completions.create(
            model="microsoft/Phi-3-mini-4k-instruct",
            messages=user_conversations[uid],
            max_tokens=500,
            temperature=0.7,
        )
        reply = completion.choices[0].message["content"]
        user_conversations[uid].append({"role": "assistant", "content": reply})
        if len(reply) > 4000:
            reply = reply[:4000] + "..."
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("AI ခေါ်ရာမှာ အမှားဖြစ်သွားပါတယ်။")

# Handler များ application ထဲထည့်ပါ
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("clear", clear))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ai))

# --- Flask webhook endpoint ---
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    # Flask က async ကို သဘာဝအတိုင်း မလုပ်နိုင်လို့ ဒီလိုသုံးတယ်
    req_json = request.get_json(force=True)
    update = Update.de_json(req_json, bot)
    await application.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

@app.route("/set_webhook")
def set_webhook():
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_NAME', 'your-app.onrender.com')}/{TELEGRAM_TOKEN}"
    # Render မှာ လက်ရှိ hostname ရဖို့ request.host ကိုသုံးပါ
    # ဒါမှမဟုတ် RENDER_EXTERNAL_URL environment variable ကိုသုံးနိုင်ပါတယ်
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
