import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.decorators import authorized
from llm.agent import Agent
from llm.memory import PersistedWindowBufferMemory
from llm.tools import CalculatorTool, TimeTool


@authorized
async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handler for incoming messages."""

    logger = logging.getLogger(__name__)
    logger.info(f"Received message: {update.message.text}")

    agent = Agent(
        system_prompt="You are Mowzio, an AI assistant capable of using tools to answer questions and fulfill requests for Amin.",
        tools=[CalculatorTool(), TimeTool()],
        memory=PersistedWindowBufferMemory(),
    )
    response = agent.process(update.message.text)
    await update.message.reply_text(response)
