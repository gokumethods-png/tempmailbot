import os
import asyncio
import random
import string
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
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

API = "https://api.mail.tm"

users = {}

# ----------------

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Online"

def web():

    app_web.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "10000"
            )
        )
    )

def keep():

    Thread(
        target=web,
        daemon=True
    ).start()

# ----------------

def rand(n=8):

    return "".join(

        random.choice(

            string.ascii_lowercase +

            string.digits

        )

        for _ in range(n)

    )

# ----------------

def generate():

    try:

        domains = requests.get(

            f"{API}/domains"

        ).json()

        domain = domains[

            "hydra:member"

        ][0][

            "domain"

        ]

        email = (

            f"{rand()}@{domain}"

        )

        password = rand(10)

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

        ).json()

        if "token" not in token:

            return None

        return (

            email,

            token["token"]

        )

    except:

        return None

# ----------------

def inbox(token):

    try:

        r = requests.get(

            f"{API}/messages",

            headers={

                "Authorization":

                f"Bearer {token}"

            }

        )

        return r.json()[

            "hydra:member"

        ]

    except:

        return []

# ----------------

async def start(

    update,

    context

):

    kb = [

        [

            InlineKeyboardButton(

                "📧 Generate",

                callback_data="g"

            )

        ],

        [

            InlineKeyboardButton(

                "📥 Inbox",

                callback_data="i"

            )

        ]

    ]

    await update.message.reply_text(

        "🔥 TempMail Bot",

        reply_markup=

        InlineKeyboardMarkup(

            kb

        )

    )

# ----------------

async def click(

    update,

    context

):

    q = update.callback_query

    await q.answer()

    uid = q.from_user.id

    if q.data == "g":

        res = generate()

        if not res:

            await q.message.reply_text(

                "❌ Failed"

            )

            return

        email, token = res

        users[uid] = (

            email,

            token

        )

        await q.message.reply_text(

            f"📧 `{email}`",

            parse_mode="Markdown"

        )

    else:

        if uid not in users:

            await q.message.reply_text(

                "Generate first"

            )

            return

        mail = inbox(

            users[uid][1]

        )

        if not mail:

            await q.message.reply_text(

                "📭 Empty"

            )

            return

        text = ""

        for m in mail:

            text += (

                f"📨 "

                f"{m['subject']}\n"

            )

        await q.message.reply_text(

            text

        )

# ----------------

async def main():

    keep()

    bot = (

        Application

        .builder()

        .token(

            BOT_TOKEN

        )

        .build()

    )

    bot.add_handler(

        CommandHandler(

            "start",

            start

        )

    )

    bot.add_handler(

        CallbackQueryHandler(

            click

        )

    )

    await bot.initialize()

    await bot.start()

    await bot.updater.start_polling()

    while True:

        await asyncio.sleep(

            999999

        )

asyncio.run(
    main()
)
