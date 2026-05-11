import os
import asyncio
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

# Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

# ... (A. အပိုင်း ပြီးဆုံးခြင်း)
# ... (A. အပိုင်း ဆက်လက်ခြင်း)

# Hugging Face Client
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)
# Conversation Memory
user_conversations = {}

# ... (B. အပိုင်း ပြီးဆုံးခြင်း)
# ... (B. အပိုင်း ဆက်လက်ခြင်း)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ။ ကျွန်တော်က Hugging Face AI Bot ပါ။",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - စတင်ရန်\n/clear - မှတ်ဉာဏ်ရှင်းရန်")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    await update.message.reply_text("စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။")

# ... (C. အပိုင်း ပြီးဆုံးခြင်း)
# ... (C. အပိုင်း ဆက်လက်ခြင်း)

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
# ... (D. အပိုင်း ပြီးဆုံးခြင်း)
# ... (D. အပိုင်း ဆက်လက်ခြင်း)

# Setup Bot Application
ptb_app = Application.builder().token(TELEGRAM_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("help", help_command))
ptb_app.add_handler(CommandHandler("clear", clear))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ai))

# Starlette App for Webhook
async def health(request):
    return PlainTextResponse("OK")

async def set_webhook(request):
    # Set Webhook URL
    webhook_url = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
    await ptb_app.bot.set_webhook(webhook_url)
    return JSONResponse({"status": "webhook set"})

async def webhook(request):
    # Receive Webhook update
    req_json = await request.json()
    update = Update.de_json(req_json, ptb_app.bot)
    await ptb_app.process_update(update)
    return JSONResponse({"status": "ok"})

starlette_app = Starlette(routes=[
    Route("/health", health),
    Route("/set_webhook", set_webhook),
    Route("/webhook", webhook, methods=["POST"]),
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
