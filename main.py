import logging
import sys
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN
import database
from reminder_scheduler import start_scheduler
from bot import start_command, tasks_command, handle_message, callback_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    logger.info("Starting Background Reminder Watchdog inside event loop...")
    start_scheduler(application)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("\n❌ ERROR: TELEGRAM_BOT_TOKEN is not configured in .env file!")
        print("Please copy .env.example to .env and insert your token from @BotFather on Telegram.\n")
        sys.exit(1)

    logger.info("Initializing Database...")
    database.init_db()

    logger.info("Building Telegram Application...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("tasks", tasks_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error Logger
    app.add_error_handler(error_handler)

    logger.info("🚀 Minimal Task & Reminder Bot is up and running! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
