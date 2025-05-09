from http import HTTPStatus
import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse
from telegram import Update

from bot.ptb import ptb

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ping")
async def ping():
    """Simple ping endpoint to check if the server is running."""
    return Response(status_code=HTTPStatus.OK, content="pong")


@router.post("/telegram/webhook")
async def process_update(request: Request):
    """Process incoming Telegram updates."""
    try:
        req = await request.json()
        update = Update.de_json(req, ptb.bot)
        await ptb.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        # Attempt to send an error message back to the user
        if update and update.message and update.message.chat_id:
            try:
                await ptb.bot.send_message(
                    chat_id=update.message.chat_id,
                    text="Oopsie! It seems your broke something with your request :(. Please try again later!",
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message to user: {send_error}")
    return Response(status_code=HTTPStatus.OK)


@router.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("templates/index.html")
