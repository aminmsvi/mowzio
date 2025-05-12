from telegram.ext import CommandHandler, MessageHandler, filters

from bot.handlers import amnesia, currensee, digin, handle_message, start
from bot.ptb import ptb


# Add handlers to the application
def register_handlers():
    ptb.add_handler(CommandHandler("start", start))
    ptb.add_handler(CommandHandler("amnesia", amnesia))
    ptb.add_handler(CommandHandler("currensee", currensee))
    ptb.add_handler(CommandHandler("digin", digin))
    ptb.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
