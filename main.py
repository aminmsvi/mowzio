from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.api.routes import router as api_router
from bot.ptb import ptb
from bot.handlers import register_handlers

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage the lifespan of the application, setting the webhook and starting/stopping the bot."""
    await ptb.bot.setWebhook(settings.TELEGRAM_WEBHOOK_URL)
    register_handlers()
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan, title="Mowzio Bot")

# Include API routes
app.include_router(api_router)