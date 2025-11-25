import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock pytesseract and PIL
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()

from utils.ocr_helper import OCRHelper

class TestOCRHelper(unittest.TestCase):
    def setUp(self):
        self.helper = OCRHelper()

    def test_generate_filename(self):
        text = "Recette de Gateau au Chocolat Facile"
        original_ext = ".png"
        
        # Test 1: Standard case
        name = self.helper.generate_filename(text, original_ext, max_words=3)
        self.assertEqual(name, "Recette_Gateau_Chocolat.png")
        
        # Test 2: Stopwords filtering
        text2 = "The quick brown fox"
        name2 = self.helper.generate_filename(text2, original_ext, max_words=2)
        self.assertEqual(name2, "Quick_Brown.png")
        
        # Test 3: Empty/No valid words
        text3 = "..."
        name3 = self.helper.generate_filename(text3, original_ext)
        self.assertEqual(name3, "OCR_Scan.png")

if __name__ == "__main__":
    unittest.main()
