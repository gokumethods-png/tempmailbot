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

MAIL_API = "https://api.mail.tm"

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Online"

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

def rand(n=10):
    return "".join(
        random.choices(
            string.ascii_lowercase +
            string.digits,
            k=n
        )
    )

def create_mail():

    domains = requests.get(
        f"{MAIL_API}/domains"
    ).json()["hydra:member"]

    domain = domains[0]["domain"]

    email = f"{rand()}@{domain}"

    password = rand(12)

    requests.post(
        f"{MAIL_API}/accounts",
        json={
            "address": email,
            "password": password
        }
    )

    token = requests.post(
        f"{MAIL_API}/token",
        json={
            "address": email,
            "password": password
        }
    ).json()["token"]

    return email, token

def get_inbox(token):

    headers = {
        "Authorization":
        f"Bearer {token}"
    }

    msgs = requests.get(
        f"{MAIL_API}/messages",
        headers=headers
    ).json()["hydra:member"]

    return msgs

async def start(update, context):

    keyboard = [
        [
            InlineKeyboardButton(
                "📧 Generate",
                callback_data="gen"
            )
        ],
        [
            InlineKeyboardButton(
                "📥 Inbox",
                callback_data="inbox"
            )
        ]
    ]

    await update.message.reply_text(
        "🔥 TempMail Bot",
        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )

async def buttons(update, context):

    q = update.callback_query

    await q.answer()

    uid = q.from_user.id

    if q.data == "gen":

        email, token = create_mail()

        users[uid] = {
            "mail": email,
            "token": token
        }

        await q.message.reply_text(
            f"📧 `{email}`",
            parse_mode="Markdown"
        )

    elif q.data == "inbox":

        if uid not in users:

            await q.message.reply_text(
                "Generate mail first"
            )

            return

        inbox = get_inbox(
            users[uid]["token"]
        )

        if not inbox:

            await q.message.reply_text(
                "📭 Inbox empty"
            )

            return

        text = ""

        for msg in inbox:

            text += (
                f"📨 {msg['subject']}\n"
                f"👤 {msg['from']['address']}\n\n"
            )

        await q.message.reply_text(
            text[:3500]
        )

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

asyncio.run(main())
