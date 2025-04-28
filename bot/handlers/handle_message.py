import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings
from bot.decorators import authorized
from llm.agent import Agent
from llm.client import LlmClientFactory
from llm.memory import WindowBufferedMemory
from llm.tools import CalculatorTool, TimeTool


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
    agent = Agent(client_factory=client_factory, tools=tools)
    response = agent.process(update.message.text)
    await update.message.reply_text(response)
