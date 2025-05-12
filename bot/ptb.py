from telegram.ext import Application
from config import settings

# Initialize python telegram bot using settings
ptb = Application.builder().updater(None).token(settings.TELEGRAM_BOT_TOKEN).build()
