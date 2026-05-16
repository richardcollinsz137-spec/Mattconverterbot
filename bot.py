import os
import logging
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Absolute strict logging output to system console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers instantly when /start is hit."""
    logger.info(f"Start command received from user: {update.effective_user.id}")
    
    welcome_text = (
        "You have arrived at the fastest Crypto Casino... "
        "Fast Signup, Instant Withdrawals and Exclusive VIP Benefits! "
        "Start playing now; https://betplay.io"
    )
    
    # We send text cleanly without markdown flags to guarantee zero parser hangs
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        disable_web_page_preview=False
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs any hidden system errors preventing messages from sending."""
    logger.error(f"Exception encountered while handling an update: {context.error}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.critical("CRITICAL: BOT_TOKEN environment variable is completely empty!")
        sys.exit(1)
        
    logger.info("Initializing Matt Bot structural build...")
    
    # Build application with fallback parameters
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(error_handler)
    
    logger.info("Connecting to Telegram servers... Bot is now active.")
    
    # drop_pending_updates ignores older text spam and forces immediate responsiveness
    app.run_polling(drop_pending_updates=True)
