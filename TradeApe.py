import asyncio
import json
import logging
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.urls import path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from uuid import uuid4
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOKEN = '7654506914:AAHbKM7zHvsoXv4yPGoVdiF7qVp6R9V79S8'
WEBHOOK_URL = "https://tradeape.onrender.com"  # Update with actual URL
PORT = 8000

# Initialize Telegram bot application
telegram_app = Application.builder().token(TOKEN).build()

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start command received from user {update.message.chat.id}")
    await update.message.reply_text('Welcome to TradeApe Bot! 🦍 Start trading Tokens on Stacks.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/help command received from user {update.message.chat.id}")
    await update.message.reply_text('Use /price to check Token prices, /trade to trade, /balance for your tokens, /pool for liquidity info.')

# Message Handler
def handle_response(text: str) -> str:
    if 'hello' in text.lower():
        return 'Hey there!'
    if 'how are you' in text.lower():
        return 'I am good'
    if 'i love TradeApe' in text.lower():
        return 'Remember to Trade today!'
    return 'I do not understand'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message.text
    response: str = handle_response(text)
    await update.message.reply_text(response)

# Webhook endpoint to process incoming updates
async def telegram(request: HttpRequest) -> HttpResponse:
    """Process incoming updates from Telegram."""
    await telegram_app.update_queue.put(
        Update.de_json(data=json.loads(request.body), bot=telegram_app.bot)
    )
    return HttpResponse()

# Health check endpoint
async def healthcheck(_: HttpRequest) -> HttpResponse:
    return HttpResponse("The bot is still running fine :)")

# Set URL paths for Django
urlpatterns = [
    path("telegram", telegram, name="Telegram updates"),
    path("healthcheck", healthcheck, name="Health check"),
]

# Configure Django settings
settings.configure(ROOT_URLCONF=__name__, SECRET_KEY=uuid4().hex)

# Main function to run bot and server
async def main() -> None:
    # Register command and message handlers
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Set webhook for Telegram
    await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")

    # Set up ASGI server
    webserver = uvicorn.Server(
        config=uvicorn.Config(app=get_asgi_application(), port=PORT, host="0.0.0.0")
    )

    # Run the bot and server
    async with telegram_app:
        await telegram_app.start()
        await webserver.serve()
        await telegram_app.stop()

if __name__ == "__main__":
    asyncio.run(main())
