from contextlib import asynccontextmanager
from http import HTTPStatus
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.ext._contexttypes import ContextTypes
from fastapi import FastAPI, Request, Response
import os

# Initialize python telegram bot
ptb = (
    Application.builder()
    .updater(None)
    .token(os.getenv("TELEGRAM_BOT_TOKEN"))
    .build()
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await ptb.bot.setWebhook(os.getenv("TELEGRAM_WEBHOOK_URL"))
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()

# Initialize FastAPI app (similar to Flask)
app = FastAPI(lifespan=lifespan)

@app.get("/ping")
async def ping():
    """Simple ping endpoint to check if the server is running."""
    return Response(status_code=HTTPStatus.OK, content="pong")


@app.post("/telegram/webhook")
async def process_update(request: Request):
    req = await request.json()
    update = Update.de_json(req, ptb.bot)
    await ptb.process_update(update)
    return Response(status_code=HTTPStatus.OK)


@app.get("/")
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Mowzio</title>
        </head>
        <body>
          <style>
            body {
              display: flex;
              justify-content: center;
              align-items: center;
              min-height: 100vh;
              margin: 0;
              background-color: #f0f0f0;
            }
          </style>
          <script src="https://unpkg.com/@dotlottie/player-component@2.7.12/dist/dotlottie-player.mjs" type="module"></script>
          <dotlottie-player src="https://lottie.host/5a102752-56ed-4e11-8f2b-52ba37b248f7/d9jjRkoBRs.lottie" background="transparent" speed="1" style="width: 300px; height: 300px" loop autoplay></dotlottie-player>
        </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

# Example handler
async def start(update, _: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text("starting...")

ptb.add_handler(CommandHandler("start", start))