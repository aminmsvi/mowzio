import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from app.config import settings
from bot.decorators import authorized
from bot.ptb import ptb
from llm.agent import Agent
from llm.client import LlmClientFactory
from llm.memory import WindowBufferedMemory
from llm.tools import CalculatorTool, TimeTool


@authorized
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    await update.message.reply_text(
        "✨ Beep bop. Mowzio’s awake! Ready to organize, assist, and maybe drop a joke or two."
    )


@authorized
async def amnesia(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for the /amnesia command."""
    memory = WindowBufferedMemory()
    memory.clear_messages()
    await update.message.reply_text("💭 Zzzzzap! All gone. I feel… strangely empty.")


@authorized
async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for incoming messages."""

    logger = logging.getLogger(__name__)
    logger.info(f"Received message: {update.message.text}")

    client_factory = LlmClientFactory(
        model=settings.LLM_CLIENT_MODEL,
        api_key=settings.LLM_CLIENT_API_KEY,
        base_url=settings.LLM_CLIENT_BASE_URL,
        memory=WindowBufferedMemory(),
    )

    tools = [CalculatorTool(), TimeTool()]
    agent = Agent(client_factory=client_factory, tools=tools, log_level=logging.DEBUG)
    response = agent.process(update.message.text)
    await update.message.reply_text(response)


# Add handlers to the application
def register_handlers():
    ptb.add_handler(CommandHandler("start", start))
    ptb.add_handler(CommandHandler("amnesia", amnesia))
    ptb.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
