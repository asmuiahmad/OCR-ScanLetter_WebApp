#!/usr/bin/env python3
"""
Test script for OCR extraction debugging
"""

import os
import logging
import sys
from PIL import Image
import re
import pytesseract

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config.ocr_utils import (
        clean_text, extract_hm_code, extract_roman_numeral,
        extract_text_with_multiple_configs, normalize_ocr_text
    )
except ImportError:
    logger.error("Failed to import modules. Make sure you're running this script from the project root.")
    sys.exit(1)

def test_ocr_extraction(image_path):
    """Test OCR extraction on a specific file"""
    try:
        logger.info(f"Testing OCR extraction on: {image_path}")
        
        # Extract text from image
        ocr_output = extract_text_with_multiple_configs(image_path)
        
        if not ocr_output:
            logger.error("No text extracted from image")
            return
            
        # Clean and normalize the text
        cleaned_text = clean_text(ocr_output)
        normalized_text = normalize_ocr_text(cleaned_text)
        
        # Print the raw and cleaned text
        logger.info("===== RAW OCR OUTPUT =====")
        logger.info(ocr_output)
        logger.info("===== CLEANED TEXT =====")
        logger.info(cleaned_text)
        logger.info("===== NORMALIZED TEXT =====")
        logger.info(normalized_text)
        
        # Test document number extraction
        logger.info("===== TESTING DOCUMENT NUMBER EXTRACTION =====")
        
        # Test various document number patterns
        patterns = [
            r'(?:Nomor|No|Nomer|NOMOR)\s*[:.\\-]?\s*(\d+)[/\s-]+([A-Za-z.]+)[.\s-]*(?:W15-A12|W15[-\s]*A12)/([A-Z0-9.]+)[/\s-]+([A-Z0-9]+)[/\s-]+(\d{4})',
            r'(\d+)[/\s-]+([A-Za-z.]+)[.\s-]*(?:W15-A12|W15[-\s]*A12)/([A-Z0-9.]+)[/\s-]+([A-Z0-9]+)[/\s-]+(\d{4})'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                logger.info(f"Pattern {i+1} matched: {match.groups()}")
                logger.info(f"Full document number: {'/'.join(match.groups())}")
            else:
                logger.info(f"Pattern {i+1} did not match")
                
        # Test HM code extraction
        hm_code = extract_hm_code(normalized_text)
        logger.info(f"HM Code: {hm_code}")
        
        # Test Roman numeral extraction
        roman_numeral = extract_roman_numeral(normalized_text)
        logger.info(f"Roman Numeral: {roman_numeral}")
        
        # Test recipient extraction
        from config.ocr_utils import extract_penerima_surat_masuk, extract_penerima_surat_keluar
        
        logger.info("===== TESTING RECIPIENT EXTRACTION =====")
        penerima_masuk = extract_penerima_surat_masuk(normalized_text)
        logger.info(f"Penerima (surat masuk): {penerima_masuk}")
        
        penerima_keluar = extract_penerima_surat_keluar(normalized_text)
        logger.info(f"Penerima (surat keluar): {penerima_keluar}")
        
        # Test with a sample text containing "Yth." followed by multiline recipient
        sample_text = """
        Nomor: 123/ABC/2023
        
        Kepada Yth. Dekan Fakultas Teknologi Informasi
        Universitas Islam Kalimantan (UNISKA)
        Muhammad Arsyad Al-Banjari Banjarmasin
        di tempat
        
        Dengan hormat,
        """
        
        logger.info("===== TESTING WITH SAMPLE TEXT =====")
        logger.info(sample_text)
        penerima_sample = extract_penerima_surat_masuk(sample_text)
        logger.info(f"Penerima (sample): {penerima_sample}")
        
    except Exception as e:
        logger.error(f"Error in test_ocr_extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_ocr_extraction(image_path)
    else:
        logger.error("Please provide an image path as an argument")
        logger.info("Example usage: python3 ocr_test_file.py static/ocr/surat_masuk/1.jpg") 