import os
import logging
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_handler import process_pdf

# Setup absolute strict logging to catch errors instantly
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers instantly when /start is pressed and sends the clean text + CTA button."""
    logger.info(f"👉 /start command detected from user ID: {update.effective_user.id}")
    try:
        welcome_text = (
            "You have arrived at the fastest Crypto Casino... "
            "Fast Signup, Instant Withdrawals and Exclusive VIP Benefits! "
            "Start playing now;"
        )
        
        # Build the exact CTA Button requested
        keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)
        logger.info("✅ Welcome message with CTA button delivered successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to send welcome message: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming PDF documents."""
    doc = update.message.document
    if doc.mime_type != 'application/pdf' and not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Error: Please send a valid PDF file.")
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
            response_msg = f"📄 **PDF Converted Successfully**\n\nHere is your extracted text 👇\n\n{extracted_text}"
            await update.message.reply_text(response_msg, parse_mode="Markdown")
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

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"🚨 Telegram Bot Framework Error: {context.error}")

def main():
    if not BOT_TOKEN:
        logger.critical("❌ CRITICAL: BOT_TOKEN environment variable is missing!")
        sys.exit(1)
        
    logger.info("Building Matt Bot core application...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register core handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Matt Bot is starting up... cleaning old updates...")
    # This prevents any loops freezing up on start
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
