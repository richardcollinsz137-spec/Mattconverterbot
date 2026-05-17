import os
import logging
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_handler import process_pdf

# Direct system stdout logging to ensure logs print live on Render's dashboard
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers instantly when /start is hit, providing the CTA button link."""
    logger.info(f"📥 [START RECEIVED] User ID: {update.effective_user.id}")
    
    welcome_text = (
        "You have arrived at the fastest Crypto Casino... "
        "Fast Signup, Instant Withdrawals and Exclusive VIP Benefits! "
        "Start playing now;"
    )
    
    # Precise Inline CTA Button implementation
    keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)
    logger.info("📤 [START SENT] Welcome message dispatched successfully.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validates and processes incoming PDF files."""
    doc = update.message.document
    
    if doc.mime_type != 'application/pdf' and not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Please send a valid PDF file.")
        return

    status_msg = await update.message.reply_text("⏳ Processing your file...")
    file_path = f"downloads/{doc.file_id}.pdf"

    try:
        file_obj = await context.bot.get_file(doc.file_id)
        os.makedirs("downloads", exist_ok=True)
        await file_obj.download_to_drive(file_path)

        extracted_text = await process_pdf(file_path)

        if not extracted_text.strip():
            await status_msg.edit_text("⚠️ The PDF appears to be empty or unreadable.")
            return

        if len(extracted_text) < 3500:
            await status_msg.delete()
            await update.message.reply_text(
                f"📄 **PDF Converted Successfully**\n\nHere is your extracted text 👇\n\n{extracted_text}",
                parse_mode="Markdown"
            )
        else:
            txt_path = f"downloads/{doc.file_id}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            await status_msg.delete()
            await update.message.reply_document(
                document=open(txt_path, 'rb'), 
                caption="📄 **PDF Converted Successfully**\n\nHere is your extracted text 👇"
            )
            if os.path.exists(txt_path):
                os.remove(txt_path)

    except Exception as e:
        logger.error(f"❌ Error processing document: {str(e)}")
        await status_msg.edit_text("❌ An unexpected error occurred while processing your file.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    """Initializes the background worker cleanly without blocking loop allocations."""
    if not BOT_TOKEN:
        logger.critical("❌ CRITICAL: BOT_TOKEN environmental variable is missing!")
        return

    logger.info("Initializing application builder context...")
    # Initialize the core application layout
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Attach tracking events
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    
    # Manual context initialization to bypass async network freezing loops
    logger.info("Starting polling interface and clearing out old queue updates...")
    await app.initialize()
    await app.updater.start_polling(drop_pending_updates=True)
    await app.start()
    
    logger.info("🚀 Matt Bot is fully listening. Connection established successfully.")
    
    # Maintain open async loops indefinitely for the Render worker instance
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution loop stopped.")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    # Use native asyncio runner logic
    asyncio.run(main())
