import pytesseract
from PIL import Image
import os
import re
from typing import List, Optional

class OCRHelper:
    def __init__(self, lang: str = 'eng+fra'):
        self.lang = lang

    def extract_text(self, image_path: str) -> str:
        """Extracts text from an image using Tesseract."""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from {image_path}: {e}")
            return ""

    def generate_filename(self, text: str, original_ext: str, max_words: int = 3) -> str:
        """Generates a filename from extracted text."""
        # 1. Clean text: remove special chars, keep alphanumeric and spaces
        clean_text = re.sub(r'[^\w\s]', '', text)
        
        # 2. Split into words
        words = clean_text.split()
        
        # 3. Filter short words/stopwords (basic list)
        stopwords = {'the', 'and', 'of', 'in', 'to', 'a', 'is', 'le', 'la', 'les', 'de', 'du', 'et', 'en', 'un', 'une'}
        filtered_words = [w for w in words if len(w) > 2 and w.lower() not in stopwords]
        
        # 4. Take top N words
        selected_words = filtered_words[:max_words]
        
        if not selected_words:
            return f"OCR_Scan{original_ext}"
            
        # 5. Join with underscores and capitalize
        new_name = "_".join([w.capitalize() for w in selected_words])
        
        return f"{new_name}{original_ext}"
