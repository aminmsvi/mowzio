import logging
import os

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.decorators import authorized
from bot.ptb import ptb
from llm import LlmInterfaceFactory, CalculatorTool, TimeTool, Agent
from llm.memory import WindowBufferedMemory


@authorized
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    await update.message.reply_text("starting...")


@authorized
async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for incoming messages."""

    logger = logging.getLogger(__name__)
    logger.info(f"Received message: {update.message.text}")

    llm_interface_factory = LlmInterfaceFactory(
        model=os.getenv("LLM_INTERFACE_MODEL"),
        api_key=os.getenv("LLM_INTERFACE_API_KEY"),
        base_url=os.getenv("LLM_INTERFACE_BASE_URL"),
        memory_strategy=WindowBufferedMemory()
    )

    tools = [CalculatorTool(), TimeTool()]
    agent = Agent(
        interface_factory=llm_interface_factory,
        tools=tools,
        log_level=logging.DEBUG
    )
    response = agent.process(update.message.text)
    await update.message.reply_text(response)


# Add handlers to the application
def register_handlers():
    ptb.add_handler(CommandHandler("start", start))
    ptb.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
