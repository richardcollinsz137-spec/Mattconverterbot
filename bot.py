import os
import logging
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Synchronize system stdout for live logs on Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Global track loop for the 6-hour nudge sequence
active_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers when a user clicks /start or boots the bot."""
    chat_id = update.effective_chat.id
    active_users.add(chat_id)
    logger.info(f"👉 /start sequence initiated by user: {chat_id}")
    
    welcome_text = (
        "WELCOME!!!\n"
        "🔥The NEXT LEVEL Crypto Casino is HERE🔥\n"
        "No KYC. No limits. No waiting.\n"
        "Just pure, fast, anonymous action.\n\n"
        "💰Insane rakeback\n"
        "⚡️Instant deposit & withdrawals\n"
        "🎰Huge game selection\n"
        "🌍Players worldwide\n\n"
        "If you’re tired of slow payouts and endless verification… this is where you switch!\n"
        "👉Join NOW and start winning today"
    )
    
    try:
        # Send photo.jpg along with text content layout
        if os.path.exists('photo.jpg'):
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=open('photo.jpg', 'rb'),
                caption=welcome_text
            )
        else:
            await context.bot.send_message(chat_id=chat_id, text=welcome_text)
            logger.warning("⚠️ photo.jpg was missing from directory. Text fallback used.")

        # Hold message block
        await context.bot.send_message(chat_id=chat_id, text="Hold on for three seconds for access link")
        
        # Exact requested delay
        await asyncio.sleep(3)
        
        # Build CTA with tracking referral link
        keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io/?ref=e55fe7b2df3d")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="🚀 Access Granted! Click the button below to register:",
            reply_markup=reply_markup
        )
        logger.info(f"✅ Onboarding routine fully delivered to {chat_id}")

    except Exception as e:
        logger.error(f"❌ Error during start sequence: {e}")

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Job process running every 6 hours automatically."""
    logger.info(f"🔄 Broadcasting automatic 6-hour tracking link update to {len(active_users)} profiles.")
    
    keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io/?ref=e55fe7b2df3d")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    reminder_text = (
        "⏰ Don't miss out on exclusive VIP benefits, instant withdrawals, and huge rakeback!\n\n"
        "Tap below to create your account now 👇"
    )
    
    for chat_id in list(active_users):
        try:
            await context.bot.send_message(chat_id=chat_id, text=reminder_text, reply_markup=reply_markup)
        except Exception as e:
            logger.warning(f"Could not reach chat profile {chat_id}: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"🚨 Internals error message: {context.error}")

def main():
    if not BOT_TOKEN:
        logger.critical("❌ Environment Error: BOT_TOKEN is empty!")
        sys.exit(1)
        
    logger.info("Building framework architecture application mapping...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers layout
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(error_handler)
    
    # Setup intervals (6 hours = 21600 seconds)
    if app.job_queue:
        app.job_queue.run_repeating(send_reminders, interval=21600, first=21600)
        logger.info("📅 Job scheduler attached successfully.")
    else:
        logger.critical("❌ Critical: JobQueue could not initialize. Check dependencies.")
        
    logger.info("🚀 Connection established. The bot is actively listening...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
