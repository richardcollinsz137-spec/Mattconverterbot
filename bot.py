import os
import logging
import sys
import asyncio
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

# Global set to keep track of user chat IDs for the 6-hour reminder system
# Note: For production with frequent restarts, consider storing these in a database/file.
active_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the sequential onboarding flow when a user clicks /start."""
    chat_id = update.effective_chat.id
    active_users.add(chat_id)
    logger.info(f"👉 /start command triggered by User ID: {update.effective_user.id}")
    
    # 1. New Promotional Text Content
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
        # 2. Send the promotional photo along with the text caption
        # Looks for 'photo.jpg' in the root directory
        if os.path.exists('photo.jpg'):
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=open('photo.jpg', 'rb'),
                caption=welcome_text
            )
        else:
            # Fallback text if the image is missing from the directory
            await context.bot.send_message(chat_id=chat_id, text=welcome_text)
            logger.warning("⚠️ photo.jpg was not found in the root directory. Sent text fallback.")

        # 3. Intermediate message
        await context.bot.send_message(chat_id=chat_id, text="Hold on for three seconds for access link")
        
        # 4. Strict 3-second delay
        await asyncio.sleep(3)
        
        # 5. Deliver CTA button with tracking referral link
        keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io/?ref=e55fe7b2df3d")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="🚀 Access Granted! Click the button below to register:",
            reply_markup=reply_markup
        )
        logger.info(f"✅ Onboarding sequence completed for user {chat_id}")

    except Exception as e:
        logger.error(f"❌ Failed to complete start sequence for user {chat_id}: {e}")

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Job callback that runs automatically every 6 hours to broadcast reminders."""
    logger.info(f"🔄 Executing scheduled 6-hour sign-up reminder broadcast to {len(active_users)} users.")
    
    keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io/?ref=e55fe7b2df3d")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    reminder_text = (
        "⏰ Don't miss out on exclusive VIP benefits, instant withdrawals, and huge rakeback!\n\n"
        "Tap below to create your account now 👇"
    )
    
    for chat_id in list(active_users):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=reminder_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Could not send reminder to chat {chat_id} (User may have blocked the bot): {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"🚨 FRAMEWORK ERROR ENCOUNTERED: {context.error}")

def main():
    if not BOT_TOKEN:
        logger.critical("❌ DEPLOYMENT FAILED: The BOT_TOKEN environment variable is totally missing!")
        sys.exit(1)
        
    logger.info("🔧 Step 1: Building Telegram application instance...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Bind handlers
    app.add_handler(CommandHandler("start", start))
    app.add_error_handler(error_handler)
    
    # 6. Initialize Job Queue for recurring reminders (6 hours = 21600 seconds)
    job_queue = app.job_queue
    job_queue.run_repeating(send_reminders, interval=21600, first=21600)
    
    logger.info("🚀 Step 2: Launching polling routine and reminder routines...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
