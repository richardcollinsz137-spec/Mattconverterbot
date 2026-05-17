import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_handler import process_pdf

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers instantly when /start is hit, sending the message and CTA button."""
    logger.info(f"Start command received from user: {update.effective_user.id}")
    
    # Text without the raw URL link since it's now embedded in the button
    welcome_text = (
        "You have arrived at the fastest Crypto Casino... "
        "Fast Signup, Instant Withdrawals and Exclusive VIP Benefits! "
        "Start playing now;"
    )
    
    # Create the CTA Inline Button
    keyboard = [[InlineKeyboardButton("Click Here", url="https://betplay.io")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with the button attached
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        reply_markup=reply_markup
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    
    if doc.mime_type != 'application/pdf' and not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Error: Please send a valid PDF file.")
        return

    status_msg = await update.message.reply_text("⏳ Processing your file...")
    file_path = f"downloads/{doc.file_id}.pdf"

    try:
        # Download file
        file_obj = await context.bot.get_file(doc.file_id)
        os.makedirs("downloads", exist_ok=True)
        await file_obj.download_to_drive(file_path)

        # Process PDF
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
        logger.error(f"Error processing document {doc.file_id}: {str(e)}")
        await status_msg.edit_text("❌ An unexpected error occurred while processing your file.")
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception encountered while handling an update: {context.error}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.critical("CRITICAL: BOT_TOKEN environment variable is completely empty!")
        sys.exit(1)
        
    logger.info("Initializing Matt Bot structural build...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_error_handler(error_handler)
    
    logger.info("Connecting to Telegram servers... Bot is now active.")
    app.run_polling(drop_pending_updates=True)
