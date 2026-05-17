import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Explicit setup to ensure logs stream directly into Render's dashboard in real-time
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fires instantly when a user sends /start."""
    logger.info(f"👉 CRITICAL LOG: /start command triggered by User ID: {update.effective_user.id}")
    
    welcome_text = (
        "You have arrived at the fastest Crypto Casino... "
        "Fast Signup, Instant Withdrawals and Exclusive VIP Benefits! "
        "Start playing now;"
    )
    
    # Inline CTA Button Structure
    keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)
    logger.info("✅ SUCCESS: Welcome message with CTA delivered to chat.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Triggers if Telegram blocks a message transmission."""
    logger.error(f"🚨 FRAMEWORK ERROR ENCOUNTERED: {context.error}")

def main():
    if not BOT_TOKEN:
        logger.critical("❌ DEPLOYMENT FAILED: The BOT_TOKEN environment variable is totally missing!")
        sys.exit(1)
        
    logger.info("🔧 Step 1: Building Telegram application instance...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Bind Core Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Step 2: Launching polling routine and flushing old message queues...")
    # drop_pending_updates=True is vital. It ignores old clicks from when the bot was offline.
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
