import os
from flask import Flask, request
from telegram import Bot, Update

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")   # ✅ ဒါမှန်တယ်

# စစ်ဆေးရန် (optional)
print(f"TELEGRAM_TOKEN exists: {bool(TELEGRAM_TOKEN)}")
print(f"HF_API_KEY exists: {bool(HF_API_KEY)}")
print(f"HF_API_KEY first 10 chars: {HF_API_KEY[:10] if HF_API_KEY else 'None'}")

# ပြီးရင် ကျန်တဲ့ code တွေ ဆက်ရေးပါ...
bot = Bot(token=TELEGRAM_TOKEN)
client = InferenceClient(provider="hf-inference", api_key=HF_API_KEY)
user_conversations = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=30)
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
        send_message(chat_id, "မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။ မေးခွန်းတစ်ခုခုမေးကြည့်ပါ။")
    elif text == "/clear":
        user_conversations[user_id] = []
        send_message(chat_id, "စကားဝိုင်းမှတ်ဉာဏ်ကို ရှင်းလင်းလိုက်ပါပြီ။")
    elif text:
        # Loading ပြရန်
        send_message(chat_id, "စဉ်းစားနေပါတယ်... ခဏစောင့်ပါ။")
        
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        user_conversations[user_id].append({"role": "user", "content": text})
        
        try:
            # Hugging Face API ခေါ်မယ် (သေချာအလုပ်လုပ်မယ့် model)
            completion = client.chat.completions.create(
                model="meta-llama/Llama-3.2-1B-Instruct",
                messages=user_conversations[user_id],
                max_tokens=300,
                temperature=0.7,
            )
            reply = completion.choices[0].message["content"]
            user_conversations[user_id].append({"role": "assistant", "content": reply})
            send_message(chat_id, reply[:4000])
        except Exception as e:
            print(f"AI Error: {e}")
            send_message(chat_id, f"AI အမှား: {str(e)[:100]} ... ကျေးဇူးပြုပြီး ခဏကြာမှ ပြန်စမ်းပါ။")
    
    return "ok"

@app.route("/")
def home():
    return "Hugging Face AI Bot is running"

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
