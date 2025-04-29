import sqlite3
from datetime import datetime
import os
import threading
from typing import Any, Dict
import urllib
import django
from django.conf import settings
from django.utils.translation import gettext as _

from asgiref.wsgi import WsgiToAsgi
import uvicorn
import asyncio

from flask import Flask

from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from asgiref.sync import sync_to_async

from pyngrok import ngrok, conf

# опционально: регион по умолчанию (eu, us и т.п.)
conf.get_default().region = "eu"

# порт берём из окружения (Render назначает его в $PORT)
port = int(os.getenv('PORT', 5000))

# поднимаем HTTP-туннель на тот же порт
tunnel = ngrok.connect(port, bind_tls=True)
DJANGO_DOMAIN_HOST = tunnel.public_url

print(f"🔗 ngrok tunnel established: {DJANGO_DOMAIN_HOST}")

api_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    return conn

# Initialize database schema and perform migrations
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure base table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()

    # Desired columns, their types/definitions, and default values for existing rows
    desired_columns = {
        'first_name':   {'definition': 'TEXT',          'default': "''"},
        'last_name':    {'definition': 'TEXT',          'default': "''"},
        'username':     {'definition': 'TEXT',          'default': "''"},
        'latitude':     {'definition': 'REAL',          'default': '0'},
        'longitude':    {'definition': 'REAL',          'default': '0'},
        'language':     {'definition': 'TEXT',          'default': "'en'"},
        'created_at':   {'definition': 'TEXT',          'default': f"'{datetime.now().isoformat()}'"},
        'updated_at':   {'definition': 'TEXT',          'default': f"'{datetime.now().isoformat()}'"},
        'is_bot':      {'definition': 'BOOLEAN',       'default': '0'},
    }

    # Fetch existing columns
    cursor.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cursor.fetchall()}

    # Track newly added columns to backfill defaults
    newly_added = []
    for col, props in desired_columns.items():
        if col not in existing:
            # Add missing column
            alter_sql = f"ALTER TABLE users ADD COLUMN {col} {props['definition']}"
            cursor.execute(alter_sql)
            newly_added.append(col)
    conn.commit()

    # Backfill default values for existing users for newly added columns
    for col in newly_added:
        default_val = desired_columns[col]['default']
        update_sql = f"UPDATE users SET {col} = {default_val} WHERE {col} IS NULL"
        cursor.execute(update_sql)
    conn.commit()
    return conn, conn.cursor()

# Initialize DB and get cursor
conn, cursor = init_db()

@sync_to_async
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

async def create_user(telegram_id, defaults):
    User = get_user_model()
    user, created = await User.objects.aget_or_create(telegram_id=telegram_id, defaults=defaults)
    return user, created

def add_get_params_to_url(url: str, user_data: Dict[str, Any]):
    query_string = urllib.parse.urlencode(user_data)
    return f"{url}?{query_string}"

# Utility to get user's language (default 'en')
def get_user_language(user_id: int) -> str:
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else 'en'

# Utility to set user's language
def set_user_language(user_id: int, lang: str) -> None:
    cursor.execute(
        'UPDATE users SET language = ?, updated_at = ? WHERE user_id = ?',
        (lang, datetime.now().isoformat(), user_id)
    )
    conn.commit()

# Handler for the /start command: registers user and sends a button to request location
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # Insert or ignore basic user info (without location/language)
    cursor.execute(
        '''INSERT OR IGNORE INTO users
           (user_id, first_name, last_name, username, created_at, updated_at, is_bot)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (user.id, user.first_name, user.last_name, user.username, datetime.now().isoformat(), datetime.now().isoformat(), user.is_bot)
    )
    conn.commit()

    # Ask for language selection first
    lang_buttons = [[KeyboardButton(text="English"), KeyboardButton(text="Русский")]]
    lang_markup = ReplyKeyboardMarkup(lang_buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        text="Please choose your language / Пожалуйста, выберите язык:",
        reply_markup=lang_markup
    )

# Handler for selecting language
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = update.effective_user
    user_info = {
        'username': f'{user_data.id}',
        'telegram_id': user_data.id,
        'telegram_language': user_data.language_code or 'en',
        'telegram_username': user_data.username[:64] if user_data.username else '',
        'first_name': user_data.first_name[:60] if user_data.first_name else '',
        'last_name': user_data.last_name[:60] if user_data.last_name else '',
        'is_bot': True if user_data.is_bot else False,
        'raw_data': user_data.to_dict(),
    }

    user, created = await create_user(telegram_id=user_data.id, defaults=user_info)

    url_params = {}

    if user:
        tokens = await get_tokens_for_user(user)
        url_params['refresh'] = tokens['refresh']
        url_params['access'] = tokens['access']

    text = update.message.text.lower()
    lang = 'en' if 'english' in text else 'ru'
    set_user_language(user.id, lang)
    # Proceed to ask location in chosen language
    location_label = "Share location" if lang == 'en' else "Поделиться геолокацией"
    info_label = "Info" if lang == 'en' else "Информация"
    map_label = "Open Map" if lang == 'en' else "Открыть карту"
    settings_label = "Open Settings" if lang == 'en' else "Открыть настройки"
    prompt = "Hi! Please share your location:" if lang == 'en' else "Привет! Поделитесь, пожалуйста, своей геолокацией:" 
    location_button = KeyboardButton(text=location_label, request_location=True)
    info_button = KeyboardButton(text=info_label)
    open_map_button = KeyboardButton(
                text=map_label,
                web_app=WebAppInfo(
                    url=add_get_params_to_url(
                        f'{DJANGO_DOMAIN_HOST}/{lang}/', url_params
                    )
                ),
            )
    open_settings_button = KeyboardButton(
                text=settings_label,
                web_app=WebAppInfo(
                    url=add_get_params_to_url(
                        f'{DJANGO_DOMAIN_HOST}/{lang}/account/user/settings/', url_params
                    )
                ),
            )
    
    # Create keyboard with buttons
    keyboard = [[location_button], [info_button], [open_map_button], [open_settings_button]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(text=prompt, reply_markup=reply_markup)

# Handler for selecting language
async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = get_user_language(user.id)
    if lang == 'en':
        info_text = (
            "This bot registers users and stores their location.\n"
            "You can share your location by clicking the button below.\n"
            "To change your language, use the /start command."
        )
    else:  
        info_text = (
            "Этот бот регистрирует пользователей и сохраняет их геолокацию.\n"
            "Вы можете поделиться своей геолокацией, нажав кнопку ниже.\n"
            "Чтобы изменить язык, используйте команду /start."
        )
    await update.message.reply_text(text=info_text)

# Handler for incoming location messages: updates user location in DB
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    location = update.message.location
    lang = get_user_language(user.id)
    if location:
        lat = location.latitude
        lon = location.longitude
        cursor.execute(
            'UPDATE users SET latitude = ?, longitude = ?, updated_at = ? WHERE user_id = ?',
            (lat, lon, datetime.now().isoformat(), user.id)
        )
        conn.commit()
        success = (
            f"Thanks for sharing your location!\nLatitude: {lat}\nLongitude: {lon}" if lang=='en'
            else f"Спасибо за геолокацию!\nШирота: {lat}\nДолгота: {lon}"
        )
        await update.message.reply_text(text=success)
    else:
        error = "Sorry, I couldn't get your location." if lang=='en' else "Не удалось получить вашу геолокацию."
        await update.message.reply_text(text=error)

# Optional: show list of registered users
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   # Fetch all users
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    if not users:
        await update.message.reply_text("No users in database yet.")
        return

    # Retrieve column names in order
    cursor.execute("PRAGMA table_info(users)")
    column_names = [col[1] for col in cursor.fetchall()]

    # Build message lines
    msg_lines = ["Registered users:"]
    for user in users:
        for idx, value in enumerate(user):
            msg_lines.append(f"{column_names[idx]}: {value};")
        msg_lines.append("")  # blank line between users
    msg_lines.append(f"Total users: {len(users)}")

    await update.message.reply_text("\n".join(msg_lines))

# Handler for other text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = get_user_language(user.id)
    default = (
        "Use /start to register, set language and share your location."
        if lang=='en' else
        "Используйте /start для регистрации, выбора языка и отправки геолокации."
    )
    await update.message.reply_text(text=default)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")


def main() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    bot_app = ApplicationBuilder().token(api_token).build()

    # Register handlers
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(MessageHandler(filters.Regex('(?i)English|Русский'), handle_language))
    bot_app.add_handler(MessageHandler(filters.Regex('(?i)Info|Информация'), handle_info))
    bot_app.add_handler(CommandHandler('users', list_users))
    bot_app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # error handler
    # bot_app.add_error_handler(error_handler)

    print("Bot is polling for updates...")
    bot_app.run_polling(stop_signals=None)


# Flask-заглушка
web_app = Flask(__name__)
# wrap the Flask app in a little ASGI shim:
asgi_app = WsgiToAsgi(web_app)

@web_app.route('/')
def index():
    return "Bot is running!", 200

if __name__ == '__main__':
    bot_thread = threading.Thread(target=main, daemon=True)
    bot_thread.start()

    uvicorn.run(
        asgi_app,                        # это наш ASGI-обёрнутый Flask
        host="0.0.0.0",
        port=int(os.getenv('PORT', 5000)),
    )
