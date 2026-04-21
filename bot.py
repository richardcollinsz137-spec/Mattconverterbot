import os
import logging
import asyncio
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_handler import extract_text_from_pdf

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Hello! I'm Matt, your PDF-to-Text Bot.**\n\n"
        "Send me any PDF file, and I will extract the text for you. "
        "I can even handle scanned documents using OCR!"
    )
    await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.MARKDOWN)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    
    if file.mime_type != 'application/pdf':
        await update.message.reply_text("❌ Please send a valid PDF file.")
        return

    processing_msg = await update.message.reply_text("⏳ Processing your file...")
    
    try:
        # Download file
        pdf_file = await file.get_file()
        file_path = f"temp_{file.file_id}.pdf"
        await pdf_file.download_to_drive(file_path)

        # Extract Text
        extracted_text = await extract_text_from_pdf(file_path)
        
        if not extracted_text:
            await processing_msg.edit_text("⚠️ Could not extract text. The PDF might be empty or corrupted.")
        elif len(extracted_text) < 4000:
            await processing_msg.delete()
            await update.message.reply_text(f"📄 **PDF Converted Successfully**\n\n{extracted_text}")
        else:
            # Send as file if too long
            await processing_msg.edit_text("📄 Text is long. Sending as a .txt file...")
            text_filename = f"extracted_{file.file_unique_id}.txt"
            with open(text_filename, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            await update.message.reply_document(document=open(text_filename, "rb"), caption="✅ Extraction Complete")
            os.remove(text_filename)

    except Exception as e:
        logging.error(f"Handler Error: {e}")
        await update.message.reply_text("❌ An error occurred while processing the file.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in environment variables.")
        exit(1)
        
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    
    print("Matt Bot is running...")
    app.run_polling()
