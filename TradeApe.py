import asyncio
import logging
from flask import Flask, Response, request, abort
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.wsgi import WsgiToAsgi
import uvicorn
from http import HTTPStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOKEN = '7654506914:AAHbKM7zHvsoXv4yPGoVdiF7qVp6R9V79S8'
WEBHOOK_URL = "https://tradeape.onrender.com/webhook"  # Replace with your actual URL
PORT = 8000

# Initialize Telegram bot application
telegram_app = Application.builder().token(TOKEN).build()

# Initialize Flask app
flask_app = Flask(__name__)

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

# Webhook route
@flask_app.post("/telegram")
async def telegram_webhook() -> Response:
    """Process incoming updates from Telegram."""
    await telegram_app.update_queue.put(Update.de_json(data=request.json, bot=telegram_app.bot))
    return Response(status=HTTPStatus.OK)

# Health check route
@flask_app.route("/healthcheck")
async def healthcheck() -> Response:
    return Response("The bot is still running fine :)", status=HTTPStatus.OK)

# Set webhook route
@flask_app.route("/set_webhook")
async def set_webhook():
    success = await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")
    if success:
        logger.info("Webhook set successfully.")
        return Response("Webhook set successfully!", status=HTTPStatus.OK)
    else:
        logger.error("Webhook setup failed.")
        return Response("Webhook setup failed!", status=HTTPStatus.INTERNAL_SERVER_ERROR)

# Run the bot application and web server together
async def main():
    telegram_app.add_handler(CommandHandler('start', start_command))
    telegram_app.add_handler(CommandHandler('help', help_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    webserver = uvicorn.Server(
        config=uvicorn.Config(app=WsgiToAsgi(flask_app), port=PORT, host="0.0.0.0")
    )
    
    # Start both application and webserver
    async with telegram_app:
        await telegram_app.start()
        await webserver.serve()
        await telegram_app.stop()

if __name__ == '__main__':
    asyncio.run(main())