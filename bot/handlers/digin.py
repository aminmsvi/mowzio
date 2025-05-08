from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import authorized


@authorized
async def digin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /digin command.
    """
    await update.message.reply_text("Digin is not implemented yet.")
