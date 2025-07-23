import os
import threading
from typing import Any, Dict
import urllib
import django
from django.utils.translation import gettext as _

from django.core.asgi import get_asgi_application

import uvicorn
import asyncio

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from asgiref.sync import sync_to_async
from applications.account.models import MapMarker

from pyngrok import ngrok, conf

# опционально: регион по умолчанию (eu, us и т.п.)
conf.get_default().region = "eu"

# берём из окружения (.env файл)
port = int(os.getenv('PORT', 5000))
api_token = os.getenv('TELEGRAM_BOT_TOKEN')

# поднимаем HTTP-туннель
tunnel = ngrok.connect(port, bind_tls=True)
DJANGO_DOMAIN_HOST = tunnel.public_url

print(f"🔗 ngrok tunnel established: {DJANGO_DOMAIN_HOST}")

User = get_user_model()

@sync_to_async
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@sync_to_async
def get_first_marker(user):
    return MapMarker.objects.filter(user=user).first()

def add_get_params_to_url(url: str, user_data: Dict[str, Any]):
    query_string = urllib.parse.urlencode(user_data)
    return f"{url}?{query_string}"

# Utility to set user's language
@sync_to_async
def set_user_language(user_id: int, lang: str) -> None:
    user = User.objects.get(telegram_id=user_id)
    user.telegram_language = lang
    user.save()

# Fetching or creating a user in the database
async def create_user(telegram_id, defaults):
    User = get_user_model()
    user, created = await User.objects.aget_or_create(telegram_id=telegram_id, defaults=defaults)
    return user, created

async def get_user(user_data: Update.effective_user) -> None:
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

    return user, created

# Handler for the /start command: registers user and sends a button to request location
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await get_user(update.effective_user)

    # Ask for language selection
    lang_buttons = [[KeyboardButton(text="English"), KeyboardButton(text="Русский")]]
    lang_markup = ReplyKeyboardMarkup(lang_buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        text="Please choose your language / Пожалуйста, выберите язык:",
        reply_markup=lang_markup
    )

# Handler for selecting language
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user, created = await get_user(update.effective_user)

    url_params = {}

    if user:
        tokens = await get_tokens_for_user(user)
        url_params['refresh'] = tokens['refresh']
        url_params['access'] = tokens['access']

    text = update.message.text.lower()
    lang = 'en' if 'english' in text else 'ru'
    await set_user_language(user.telegram_id, lang)

    # Some translations
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
    user, created = await get_user(update.effective_user)
    lang = user.telegram_language or 'en' 
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
    user, created = await get_user(update.effective_user)
    marker = await get_first_marker(user)
    location = update.message.location
    lang = user.telegram_language or 'en'
    if location:
        lat = location.latitude
        lon = location.longitude
        marker.latitude = lat
        marker.longitude = lon
        await sync_to_async(user.save)()
        await sync_to_async(marker.save)()
        success = (
            f"Спасибо за геолокацию!\nШирота: {lat}\nДолгота: {lon}" if lang=='ru'
            else f"Thanks for sharing your location!\nLatitude: {lat}\nLongitude: {lon}"
        )
        await update.message.reply_text(text=success)
    else:
        error = "Не удалось получить вашу геолокацию." if lang=='ru' else "Sorry, I couldn't get your location."
        await update.message.reply_text(text=error)

# Optional: show list of registered users
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = await sync_to_async(list)(User.objects.all())

    if not users:
        await update.message.reply_text("No users in database yet.")
        return

    # Build message lines
    msg_lines = ["Registered users:"]
    for user in users:
        marker = await get_first_marker(user)
        msg_lines.append(
            f"ID: {user.id}; \n"
            f"Telegram ID: {user.telegram_id}; \n"
            f"Username: {user.telegram_username}; \n"
            f"First Name: {user.first_name}; \n"
            f"Last Name: {user.last_name}; \n"
            f"Language: {user.telegram_language}; \n"
            f"Latitude: {marker.latitude if marker else 'N/A'}; \n"
            f"Longitude: {marker.longitude if marker else 'N/A'};"
        )
        msg_lines.append("")  # blank line between users

    msg_lines.append(f"Total users: {len(users)}")

    await update.message.reply_text("\n".join(msg_lines))

# Handler for other text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = user.telegram_language or 'en'
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


asgi_app = get_asgi_application()


if __name__ == '__main__':
    bot_thread = threading.Thread(target=main, daemon=True)
    bot_thread.start()

    uvicorn.run(
    asgi_app,
    host="0.0.0.0",
    port=port,
)
