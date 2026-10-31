import os
import telebot
from flask import Flask, request
from openai import OpenAI

# ==========================================
# 1. Fetch Environment Variables
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
# Render.com automatically provides this variable with your app's URL (e.g., https://your-app.onrender.com)
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("BOT_TOKEN or HF_TOKEN is missing in Environment Variables!")

# ==========================================
# 2. Initialize Bot, Flask, and OpenAI Client
# ==========================================
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Initialize OpenAI client pointing to Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# ==========================================
# 3. Setup Telegram Webhook
# ==========================================
# Automatically connect Telegram to your Render URL when the app starts
if RENDER_EXTERNAL_URL:
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_EXTERNAL_URL)

# ==========================================
# 4. Flask Routes
# ==========================================
# This route handles incoming messages from Telegram
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

# Health check route so Render knows your app is alive
@app.route('/')
def index():
    return "Telegram Bot is running smoothly!", 200

# ==========================================
# 5. Bot Message Handler
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Show a "typing..." indicator in Telegram
        bot.send_chat_action(message.chat.id, 'typing')

        # Send user's message to Hugging Face API
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita", # Model based on your provided snippet
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
        )

        # Extract the AI's response text
        reply_text = response.choices[0].message.content

        # Send the response back to the user
        bot.reply_to(message, reply_text)

    except Exception as e:
        bot.reply_to(message, f"Oops! Something went wrong: {str(e)}")

# ==========================================
# 6. Start the Server
# ==========================================
if __name__ == "__main__":
    # Render assigns a dynamic PORT via environment variables
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
