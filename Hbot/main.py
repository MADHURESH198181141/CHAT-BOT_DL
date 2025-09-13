# main.py

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from rag_backend import get_rag_response
from contextlib import asynccontextmanager
# --- IMPORTANT: REPLACE WITH YOUR TOKEN ---
TELEGRAM_BOT_TOKEN = "8429277055:AAEFSz9v0BLk9oVatdE8QVWO-TiPvACAlSU"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await application.initialize()
    yield
    await application.shutdown()

# --- Application Setup ---
app = FastAPI(lifespan=lifespan)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! I am the Odisha Public Health Bot. Please ask me your health-related questions.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    # The bot's reply to "Thinking..." will have a message_id that is one greater than the user's message
    thinking_message = await update.message.reply_text("Thinking...")
    
    response = get_rag_response(query)
    
    # Edit the "Thinking..." message with the final answer
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=thinking_message.message_id,
        text=response
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook Endpoint ---
@app.post("/")
async def process_update(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

# --- MAIN ENTRY POINT (THE NEW PART) ---
# This block will only run when you execute `python main.py`
if __name__ == "__main__":
    # This command starts the Uvicorn server programmatically
    uvicorn.run(
        "main:app",  # The application to run, as a string
        host="127.0.0.1",  # The host to bind to
        port=8000,  # The port to listen on
        reload=True  # Automatically reload on code changes (for development)
    )