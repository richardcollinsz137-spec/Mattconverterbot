import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_handler import process_pdf

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the configured crypto casino marketing welcome message."""
    welcome_text = (
        "You have arrived at the fastest Crypto Casino... "
        "Fast Signup, Instant Withdrawals and Exclusive VIP Benefits! "
        "Start playing now; https://betplay.io"
    )
    await update.message.reply_text(welcome_text, disable_web_page_preview=False)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validates, downloads, and processes received PDF files."""
    doc = update.message.document
    
    # Strictly handle PDF mime types
    if doc.mime_type != 'application/pdf' and not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Error: Please send a valid PDF file.")
        return

    status_msg = await update.message.reply_text("⏳ Processing your file...")
    file_path = f"downloads/{doc.file_id}.pdf"

    try:
        # Secure the file download
        file_obj = await context.bot.get_file(doc.file_id)
        os.makedirs("downloads", exist_ok=True)
        await file_obj.download_to_drive(file_path)

        # Offload intensive processing to the PDF handler
        extracted_text = await process_pdf(file_path)

        if not extracted_text.strip():
            await status_msg.edit_text("⚠️ The PDF appears to be empty or completely unreadable.")
            return

        # Smart response formatting based on character limits (Telegram cap is ~4096)
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
        # Always clean up system disk storage to prevent memory/storage leaks on Render
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN environment variable is missing. Exiting.")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
        
        logger.info("Matt Bot is running under polling mode...")
        app.run_polling()
