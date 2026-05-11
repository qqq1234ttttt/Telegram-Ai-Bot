import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

app = Flask(__name__)

@app.route('/')
def home():
    return "KMt AI Bot is running!"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)

user_conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ။ ကျွန်တော်က **KMT AI Bot** ပါ။\n\n"
        "စမ်းကြည့်ချင်ရင် တစ်ခုခုရိုက်ထည့်ပါ။",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - စတင်ရန်\n/clear - မှတ်ဉာဏ်ရှင်းရန်")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    await update.message.reply_text("စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။")

async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_message = update.message.text
    await update.message.reply_chat_action(action="typing")
    
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
        response_text = completion.choices[0].message["content"]
        user_conversations[user_id].append({"role": "assistant", "content": response_text})
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "..."
        await update.message.reply_text(response_text)
    except Exception as e:
        await update.message.reply_text("AI ခေါ်ရာမှာ အမှားဖြစ်သွားပါတယ်။ ခဏကြာမှ ပြန်စမ်းပါ။")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ai))
    application.run_polling()

if __name__ == "__main__":
    from threading import Thread
    Thread(target=main).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
