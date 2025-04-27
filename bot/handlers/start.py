from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import authorized


@authorized
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    await update.message.reply_text(
        "✨ Beep bop. Mowzio’s awake! Ready to organize, assist, and maybe drop a joke or two."
    )
