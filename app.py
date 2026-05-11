import os
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
from huggingface_hub import InferenceClient

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)
user_conversations = {}

def start(update, context):
    update.message.reply_text("မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။")

def help_command(update, context):
    update.message.reply_text("/start - စတင်ရန်\n/clear - မှတ်ဉာဏ်ရှင်းရန်")

def clear(update, context):
    user_id = update.effective_chat.id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    update.message.reply_text("စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။")

def ask_ai(update, context):
    user_id = update.effective_chat.id
    user_message = update.message.text
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append({"role": "user", "content": user_message})
    try:
        completion = client.chat.completions.create(
            model="microsoft/Phi-3-mini-4k-instruct",
            messages=user_conversations[user_id],
            max_tokens=500,
            temperature=0.7,
        )
        reply = completion.choices[0].message["content"]
        user_conversations[user_id].append({"role": "assistant", "content": reply})
        update.message.reply_text(reply[:4000])
    except Exception as e:
        update.message.reply_text("AI ခေါ်ရာမှာ အမှားဖြစ်သွားပါတယ်။")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("clear", clear))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ai))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
