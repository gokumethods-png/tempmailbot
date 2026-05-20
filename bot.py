from flask import Flask
from threading import Thread
import logging
import random
import string
import requests
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = "https://api.mail.tm"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_mails = {}

def random_string(length=10):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_domain():
    response = requests.get(f"{BASE_URL}/domains")
    return response.json()["hydra:member"][0]["domain"]

def create_account():
    domain = get_domain()
    username = random_string()
    email = f"{username}@{domain}"
    password = random_string(12)

    payload = {
        "address": email,
        "password": password
    }

    requests.post(f"{BASE_URL}/accounts", json=payload)

    token_res = requests.post(f"{BASE_URL}/token", json=payload)
    token = token_res.json()["token"]

    return {
        "email": email,
        "password": password,
        "token": token
    }

def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/messages", headers=headers)
    return response.json()["hydra:member"]

def read_message(token, msg_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers)
    return response.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📧 Generate Temp Mail", callback_data="gen")],
        [InlineKeyboardButton("📥 Check Inbox", callback_data="inbox")]
    ]

    await update.message.reply_text(
        "🔥 Welcome To Goku TempMail Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "gen":
        account = create_account()
        user_mails[user_id] = account

        await query.message.reply_text(
            f"✅ Temp Mail Generated\n\n📧 `{account['email']}`",
            parse_mode="Markdown"
        )

    elif query.data == "inbox":

        if user_id not in user_mails:
            await query.message.reply_text("❌ Generate a temp mail first")
            return

        account = user_mails[user_id]
        token = account["token"]

        messages = get_messages(token)

        if not messages:
            await query.message.reply_text("📭 Inbox is empty")
            return

        for msg in messages:
            full_msg = read_message(token, msg["id"])

            sender = msg.get("from", {}).get("address", "Unknown")
            subject = msg.get("subject", "No Subject")
            body = full_msg.get("text", "No content")

            await query.message.reply_text(
                f"📨 New Email\n\n"
                f"👤 From: {sender}\n"
                f"📝 Subject: {subject}\n\n"
                f"{body[:3500]}"
            )

async def main():
    keep_alive()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot started successfully!")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
