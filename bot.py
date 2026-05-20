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

BOT_TOKEN = os.getenv("BOT_TOKEN")

BASE_URL = "https://api.mail.tm"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

user_mails = {}

def random_string(length=10):
    return "".join(
        random.choices(
            string.ascii_lowercase + string.digits,
            k=length
        )
    )

def get_domain():
    response = requests.get(f"{BASE_URL}/domains")
    domains = response.json()["hydra:member"]
    return domains[0]["domain"]

def create_account():
    domain = get_domain()

    username = random_string()
    email = f"{username}@{domain}"
    password = random_string(12)

    payload = {
        "address": email,
        "password": password
    }

    requests.post(
        f"{BASE_URL}/accounts",
        json=payload
    )

    token_res = requests.post(
        f"{BASE_URL}/token",
        json=payload
    )

    token = token_res.json()["token"]

    return {
        "email": email,
        "password": password,
        "token": token
    }

def get_messages(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/messages",
        headers=headers
    )

    return response.json()["hydra:member"]

def read_message(token, msg_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/messages/{msg_id}",
        headers=headers
    )

    return response.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📧 Generate Temp Mail", callback_data="gen")],
        [InlineKeyboardButton("📥 Check Inbox", callback_data="inbox")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔥 Welcome To TempMail Bot\n\n"
        "Generate unlimited temporary emails instantly.",
        reply_markup=reply_markup,
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "gen":
        try:
            account = create_account()
            user_mails[user_id] = account

            email = account["email"]

            keyboard = [
                [InlineKeyboardButton("📥 Check Inbox", callback_data="inbox")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                f"✅ Temp Mail Generated\n\n📧 `{email}`",
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )

        except Exception as e:
            logger.error(e)
            await query.message.reply_text(
                "❌ Failed to generate temp mail"
            )

    elif query.data == "inbox":

        if user_id not in user_mails:
            await query.message.reply_text(
                "❌ Generate a temp mail first"
            )
            return

        try:
            account = user_mails[user_id]
            token = account["token"]

            messages = get_messages(token)

            if not messages:
                await query.message.reply_text(
                    "📭 Inbox is empty"
                )
                return

            for msg in messages:
                msg_id = msg["id"]

                sender = msg.get("from", {}).get(
                    "address",
                    "Unknown"
                )

                subject = msg.get("subject", "No Subject")

                full_msg = read_message(
                    token,
                    msg_id
                )

                body = full_msg.get(
                    "text",
                    "No content"
                )

                text = (
                    f"📨 New Email\n\n"
                    f"👤 From: {sender}\n"
                    f"📝 Subject: {subject}\n\n"
                    f"📄 Message:\n{body[:3500]}"
                )

                await query.message.reply_text(text)

        except Exception as e:
            logger.error(e)

            await query.message.reply_text(
                "❌ Failed to fetch inbox"
            )

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
