from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from app.config import settings


def authorized(handler):
    """Decorator to check if the user is authorized to use the bot."""

    @wraps(handler)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = update.effective_user
        if user and user.username == settings.TELEGRAM_AUTHORIZED_USERNAME:
            return await handler(update, context, *args, **kwargs)

        if update.message:
            await update.message.reply_text("You are not authorized to use this bot.")
            return None

    return wrapper
