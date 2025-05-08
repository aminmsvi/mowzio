from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import authorized
from llm.memory import PersistedWindowBufferMemory


@authorized
async def amnesia(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for the /amnesia command."""
    memory = PersistedWindowBufferMemory()
    memory.clear_messages()
    await update.message.reply_text("💭 Zzzzzap! All gone. I feel… strangely empty.")
