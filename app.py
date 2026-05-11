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
    """Hugging Face Free Inference API - သေချာအလုပ်ဖြစ်မယ့် model"""
    # အလုပ်ဖြစ်မယ့် free model များ (တစ်ခုပြီးတစ်ခုစမ်းပါ)
    models = [
        "google/gemma-2-2b-it",
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
        "microsoft/phi-2"
    ]
    
    for model in models:
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        try:
            print(f"Trying model: {model}")
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                    if text:
                        return text
                elif isinstance(result, dict):
                    text = result.get("generated_text", "")
                    if text:
                        return text
            elif response.status_code == 404:
                continue  # ဒီ model မရှိရင် နောက်တစ်ခုစမ်းမယ်
            else:
                print(f"Error with {model}: {response.status_code}")
        except Exception as e:
            print(f"Request Error with {model}: {e}")
            continue
    
    return "မေးခွန်းကို နားမလည်နိုင်တော့ပါဘူး။ တစ်ခါနောက်မှ ထပ်မေးပါ။"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    update = Update.de_json(req, bot)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text if update.message else ""

    if text == "/start":
        send_message(chat_id, "မင်္ဂလာပါ။ Hugging Face AI Bot ပါ။ အခုသုံးနေတဲ့မော်ဒယ်က Google Gemma ဖြစ်ပါတယ်။")
    elif text == "/clear":
        user_conversations[user_id] = []
        send_message(chat_id, "မှတ်ဉာဏ်ရှင်းပြီးပါပြီ။")
    elif text:
        send_message(chat_id, "စဉ်းစားနေပါတယ်... ခဏစောင့်ပါ။")
        
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        user_conversations[user_id].append(f"User: {text}")
        
        if len(user_conversations[user_id]) > 10:
            user_conversations[user_id] = user_conversations[user_id][-10:]
        
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
