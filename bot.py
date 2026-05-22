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

API = "https://api.mail.tm"

# =====================
# WEB
# =====================

web = Flask(__name__)

@web.route("/")
def home():
    return "TempMail Running"

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

# =====================
# STORE USERS
# =====================

users = {}

# =====================
# RANDOM
# =====================

def rand(n=10):

    return "".join(

        random.choices(

            string.ascii_lowercase +

            string.digits,

            k=n

        )

    )

# =====================
# CREATE MAIL
# =====================

def create_mail():

    domains = requests.get(

        f"{API}/domains"

    ).json()["hydra:member"]

    allowed = []

    for d in domains:

        domain = d["domain"]

        if domain != "wshu.net":

            allowed.append(
                domain
            )

    domain = random.choice(
        allowed
    )

    email = f"{rand()}@{domain}"

    password = rand(12)

    requests.post(

        f"{API}/accounts",

        json={

            "address": email,

            "password": password

        }

    )

    token = requests.post(

        f"{API}/token",

        json={

            "address": email,

            "password": password

        }

    )

    token = token.json()["token"]

    return (

        email,

        token

    )

# =====================
# INBOX
# =====================

def get_inbox(token):

    headers = {

        "Authorization":

        f"Bearer {token}"

    }

    res = requests.get(

        f"{API}/messages",

        headers=headers

    )

    return res.json().get(

        "hydra:member",

        []

    )

# =====================
# START
# =====================

async def start(

    update,

    context

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

# =====================
# BUTTONS
# =====================

async def buttons(

    update,

    context

):

    q = update.callback_query

    await q.answer()

    uid = q.from_user.id

    # Generate

    if q.data == "gen":

        email, token = create_mail()

        users[uid] = {

            "email": email,

            "token": token

        }

        await q.message.reply_text(

            f"✅ Generated\n\n"

            f"📧 `{email}`",

            parse_mode="Markdown"

        )

    # Inbox

    elif q.data == "inbox":

        if uid not in users:

            await q.message.reply_text(

                "Generate first"

            )

            return

        inbox = get_inbox(

            users[uid]["token"]

        )

        if not inbox:

            await q.message.reply_text(

                "📭 Inbox Empty"

            )

            return

        text = ""

        for mail in inbox:

            subject = mail.get(

                "subject",

                "No Subject"

            )

            sender = mail.get(

                "from",

                {}

            ).get(

                "address",

                "Unknown"

            )

            text += (

                f"📨 {subject}\n"

                f"👤 {sender}\n\n"

            )

        await q.message.reply_text(

            text[:3500]

        )

# =====================
# MAIN
# =====================

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

    while True:

        await asyncio.sleep(

            3600

        )

if __name__ == "__main__":

    asyncio.run(

        main()

    )
