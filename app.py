import os
import requests
from flask import Flask, request
from telegram import Bot, Update

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
user_conversations = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    except Exception as e:
        print(f"Send error: {e}")

def ask_huggingface(prompt):
    """Hugging Face Free Inference API ကို တိုက်ရိုက်ခေါ်တယ်"""
    api_url = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": f"<|user|>\n{prompt}\n<|assistant|>\n",
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            # response ပုံစံက [{'generated_text': '...'}] မျိုးဖြစ်တတ်တယ်
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "အဖြေမရှိပါ")
            elif isinstance(result, dict):
                return result.get("generated_text", "အဖြေမရှိပါ")
            else:
                return str(result)
        else:
            print(f"HF API Error: {response.status_code} - {response.text}")
            return f"API Error: {response.status_code}"
    except Exception as e:
        print(f"Request Error: {e}")
        return f"Request Error: {str(e)}"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    update = Update.de_json(req, bot)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text if update.message else ""

    if text == "/start":
        send_message(chat_id, "မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။ (Phi-3 model)")
    elif text == "/clear":
        user_conversations[user_id] = []
        send_message(chat_id, "မှတ်ဉာဏ်ရှင်းပြီးပါပြီ။")
    elif text:
        send_message(chat_id, "စဉ်းစားနေပါတယ်...")
        
        # Conversation memory ထဲထည့်
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        user_conversations[user_id].append(f"User: {text}")
        
        # နောက်ဆုံး ၁၀ ခေါက်ပဲ မှတ်ထားမယ် (memory အကန့်အသတ်)
        if len(user_conversations[user_id]) > 10:
            user_conversations[user_id] = user_conversations[user_id][-10:]
        
        # Conversation ကို ပေါင်းစပ်ပြီး prompt လုပ်မယ်
        full_prompt = "\n".join(user_conversations[user_id]) + "\nAssistant:"
        
        reply = ask_huggingface(full_prompt)
        user_conversations[user_id].append(f"Assistant: {reply}")
        send_message(chat_id, reply[:4000])
    
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
