import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router as api_router
from bot.handler_registery import register_handlers
from bot.ptb import ptb
from config import settings

# Configure logging first
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "formatter": "standard",
                "class": "logging.StreamHandler",
            }
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": True,
            },
            "httpcore.http11": {
                "handlers": ["default"],
                "level": "CRITICAL",
                "propagate": False,
            },
        },
    }
)


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
