import os
import random
import string
import asyncio

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

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================
# KEEP RENDER ALIVE
# ==========================

web = Flask(__name__)

@web.route("/")
def home():
    return "Generator.Email Bot Online"

def run_web():
    web.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "10000"
            )
        )
    )

def keep_alive():

    Thread(
        target=run_web,
        daemon=True
    ).start()

# ==========================
# MAIL GENERATOR
# ==========================

def generate_email():

    name = "".join(
        random.choices(
            string.ascii_lowercase +
            string.digits,
            k=10
        )
    )

    return f"{name}@generator.email"

# ==========================
# START
# ==========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "📧 Generate Mail",
                callback_data="gen"
            )
        ],
        [
            InlineKeyboardButton(
                "📥 Inbox Link",
                callback_data="inbox"
            )
        ]
    ]

    await update.message.reply_text(
        "🔥 Generator.Email TempMail",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

# ==========================
# BUTTONS
# ==========================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data == "gen":

        email = generate_email()

        context.user_data["mail"] = email

        await query.message.reply_text(
            f"✅ Temp Mail Generated\n\n"
            f"📧 `{email}`",
            parse_mode="Markdown"
        )

    elif query.data == "inbox":

        email = context.user_data.get(
            "mail"
        )

        if not email:

            await query.message.reply_text(
                "❌ Generate mail first"
            )

            return

        inbox = (
            "https://generator.email/"
            + email
        )

        await query.message.reply_text(
            f"📥 Inbox\n\n"
            f"{inbox}"
        )

# ==========================
# MAIN
# ==========================

async def main():

    keep_alive()

    app = (
        Application
        .builder()
        .token(
            BOT_TOKEN
        )
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

    print(
        "Bot started"
    )

    while True:

        await asyncio.sleep(
            3600
        )

if __name__ == "__main__":

    asyncio.run(
        main()
    )
