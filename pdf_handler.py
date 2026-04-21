import pdfplumber
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

async def extract_text_from_pdf(file_path):
    """
    Extracts text from PDF. If no text is found, attempts OCR on the first 5 pages.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Fallback to OCR if extracted text is negligible
        if len(text.strip()) < 10:
            logger.info("Minimal text found. Attempting OCR...")
            text = perform_ocr(file_path)
            
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return None

def perform_ocr(file_path):
    """OCR Fallback using Tesseract"""
    text = "[OCR Result]\n"
    try:
        with pdfplumber.open(file_path) as pdf:
            # Limit to first 5 pages for performance on free tiers
            for page in pdf.pages[:5]:
                im = page.to_image(resolution=200).original
                text += pytesseract.image_to_string(im) + "\n"
        return text
    except Exception as e:
        logger.error(f"OCR Failed: {e}")
        return ""
