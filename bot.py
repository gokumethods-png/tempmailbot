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

users = {}

# -----------------
# WEB SERVER
# -----------------

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

# -----------------
# RANDOM
# -----------------

def rand(n=10):

    return "".join(

        random.choices(

            string.ascii_lowercase +

            string.digits,

            k=n

        )

    )

# -----------------
# CREATE EMAIL
# -----------------

def create_mail():

    try:

        res = requests.get(
            f"{API}/domains",
            timeout=15
        )

        domains = res.json()

        domains = domains[
            "hydra:member"
        ]

        available = []

        for d in domains:

            name = d["domain"]

            if name != "wshu.net":

                available.append(
                    name
                )

        if not available:

            return None

        domain = random.choice(
            available
        )

        email = (

            f"{rand()}@{domain}"

        )

        password = rand(12)

        acc = requests.post(

            f"{API}/accounts",

            json={

                "address": email,

                "password": password

            },

            timeout=15

        )

        if acc.status_code not in [

            200,

            201

        ]:

            return None

        token = requests.post(

            f"{API}/token",

            json={

                "address": email,

                "password": password

            },

            timeout=15

        )

        if token.status_code != 200:

            return None

        return (

            email,

            token.json()["token"]

        )

    except Exception as e:

        print(e)

        return None

# -----------------
# INBOX
# -----------------

def inbox(token):

    try:

        headers = {

            "Authorization":

            f"Bearer {token}"

        }

        r = requests.get(

            f"{API}/messages",

            headers=headers,

            timeout=15

        )

        return r.json().get(

            "hydra:member",

            []

        )

    except:

        return []

# -----------------
# START
# -----------------

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

                callback_data="box"

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

# -----------------
# BUTTONS
# -----------------

async def buttons(

    update,

    context

):

    q = update.callback_query

    await q.answer()

    uid = q.from_user.id

    if q.data == "gen":

        result = create_mail()

        if not result:

            await q.message.reply_text(

                "❌ Generation failed"

            )

            return

        email, token = result

        users[uid] = {

            "email": email,

            "token": token

        }

        await q.message.reply_text(

            f"✅ Generated\n\n📧 `{email}`",

            parse_mode="Markdown"

        )

    elif q.data == "box":

        if uid not in users:

            await q.message.reply_text(

                "Generate first"

            )

            return

        msgs = inbox(

            users[uid]["token"]

        )

        if not msgs:

            await q.message.reply_text(

                "📭 Inbox Empty"

            )

            return

        out = ""

        for m in msgs:

            out += (

                f"📨 {m.get('subject','No Subject')}\n"

                f"👤 {m['from']['address']}\n\n"

            )

        await q.message.reply_text(

            out[:3500]

        )

# -----------------
# MAIN
# -----------------

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
