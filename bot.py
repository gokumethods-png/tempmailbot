import os
import random
import string
import asyncio
import requests

from flask import Flask
from threading import Thread

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

web = Flask(__name__)

@web.route("/")
def home():
    return "TempMail Bot Online"

def run_web():
    web.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000"))
    )

def keep_alive():
    Thread(
        target=run_web,
        daemon=True
    ).start()

users = {}

# =====================
# GENERATE MAIL
# =====================

def generate_email():

    username = "".join(
        random.choices(
            string.ascii_lowercase +
            string.digits,
            k=10
        )
    )

    return f"{username}@generator.email"

# =====================
# FETCH EMAIL
# =====================

def get_mail(email):

    try:

        url = f"https://generator.email/{email}"

        r = requests.get(
            url,
            timeout=10
        )

        if r.status_code == 200:

            return "📬 Inbox checked.\nOpen generator.email to view messages."

        return "📭 Inbox empty"

    except:
        return "❌ Failed to load inbox"

# =====================
# START
# =====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "📧 Generate",
                callback_data="gen"
            )
        ],
        [
            InlineKeyboardButton(
                "📥 Check Inbox",
                callback_data="inbox"
            )
        ]
    ]

    await update.message.reply_text(
        "🔥 TempMail Bot",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

# =====================
# BUTTONS
# =====================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    uid = query.from_user.id

    if query.data == "gen":

        email = generate_email()

        users[uid] = email

        await query.message.reply_text(
            f"✅ Generated\n\n📧 `{email}`",
            parse_mode="Markdown"
        )

    elif query.data == "inbox":

        if uid not in users:

            await query.message.reply_text(
                "Generate mail first"
            )

            return

        inbox = get_mail(
            users[uid]
        )

        await query.message.reply_text(
            inbox
        )

# =====================
# MAIN
# =====================

async def main():

    keep_alive()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    while True:

        await asyncio.sleep(
            3600
        )

if __name__ == "__main__":

    asyncio.run(
        main()
    )
