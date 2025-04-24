from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.ptb import ptb

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    await update.message.reply_text("starting...")

# Add handlers to the application
def register_handlers():
    ptb.add_handler(CommandHandler("start", start))