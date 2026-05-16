import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_handler import process_pdf

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Updated welcome text with casino branding
    welcome_text = (
        "🎰 **You have arrived at the fastest Crypto Casino...**\n\n"
        "⚡ Fast Signup, Instant Withdrawals and Exclusive VIP Benefits!\n\n"
        "🚀 Start playing now: https://betplay.io"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", disable_web_page_preview=False)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    
    if doc.mime_type != 'application/pdf':
        await update.message.reply_text("❌ Please send a valid PDF file.")
        return

    status_msg = await update.message.reply_text("⏳ Processing your file...")

    try:
        # Download file
        file_obj = await context.bot.get_file(doc.file_id)
        file_path = f"downloads/{doc.file_id}.pdf"
        os.makedirs("downloads", exist_ok=True)
        await file_obj.download_to_drive(file_path)

        # Process PDF
        extracted_text = await process_pdf(file_path)

        if not extracted_text.strip():
            await status_msg.edit_text("⚠️ The PDF appears to be empty or unreadable.")
        elif len(extracted_text) < 4000:
            await status_msg.delete()
            await update.message.reply_text(f"📄 **PDF Converted Successfully**\n\n{extracted_text}")
        else:
            # Long text -> Send as .txt file
            txt_path = f"downloads/{doc.file_id}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            await status_msg.delete()
            await update.message.reply_document(document=open(txt_path, 'rb'), caption="📄 Text too long for a message. Here is the file!")
            os.remove(txt_path)

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text("❌ An error occurred while processing your file.")
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
        
        print("Matt Bot is running...")
        app.run_polling()
