from http import HTTPStatus
from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse
from telegram import Update
from bot.ptb import ptb

router = APIRouter()


@router.get("/ping")
async def ping():
    """Simple ping endpoint to check if the server is running."""
    return Response(status_code=HTTPStatus.OK, content="pong")


@router.post("/telegram/webhook")
async def process_update(request: Request):
    """Process incoming Telegram updates."""
    req = await request.json()
    update = Update.de_json(req, ptb.bot)
    await ptb.process_update(update)
    return Response(status_code=HTTPStatus.OK)


@router.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("templates/index.html")
