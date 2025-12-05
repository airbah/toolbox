import os
import re
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.settings_manager import settings

# PDF Libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# OCR
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Word documents
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class FileType(Enum):
    PDF = "pdf"
    IMAGE = "image"
    WORD = "word"
    UNKNOWN = "unknown"


@dataclass
class InvoiceResult:
    """Result of invoice detection for a file."""
    file_path: str
    file_name: str
    is_invoice: bool
    confidence_score: float
    company_name: Optional[str]
    extracted_text: str
    detected_keywords: List[str]
    error: Optional[str] = None


class InvoiceDetector:
    """Detects invoices and extracts company names from documents."""
    
    # Keywords for invoice detection (French & English)
    INVOICE_KEYWORDS = {
        'facture': 15,
        'invoice': 15,
        'reçu': 10,
        'receipt': 10,
        'bon de commande': 8,
        'purchase order': 8,
        'total ttc': 12,
        'total ht': 12,
        'montant': 8,
        'amount': 8,
        'tva': 10,
        'vat': 10,
        'n° facture': 15,
        'facture n°': 15,
        'invoice #': 15,
        'invoice no': 15,
        'date de facture': 10,
        'invoice date': 10,
        'siret': 12,
        'siren': 12,
        'rcs': 10,
        'numéro de client': 8,
        'customer number': 8,
        'référence': 6,
        'reference': 6,
        'échéance': 8,
        'due date': 8,
        'paiement': 6,
        'payment': 6,
    }
    
    # Legal entity suffixes for company detection
    LEGAL_ENTITIES = [
        'sarl', 's.a.r.l', 'sas', 's.a.s', 'sa', 's.a', 'eurl', 'e.u.r.l',
        'sasu', 'snc', 'sci', 'scop', 'scea', 'gmbh', 'ltd', 'llc', 'inc',
        'corp', 'plc', 'ag', 'bv', 'nv'
    ]
    
    # Known companies (common invoices)
    KNOWN_COMPANIES = {
        'amazon': 'Amazon',
        'google': 'Google',
        'microsoft': 'Microsoft',
        'apple': 'Apple',
        'orange': 'Orange',
        'free': 'Free',
        'sfr': 'SFR',
        'bouygues': 'Bouygues',
        'edf': 'EDF',
        'engie': 'Engie',
        'total': 'Total',
        'carrefour': 'Carrefour',
        'leclerc': 'Leclerc',
        'auchan': 'Auchan',
        'lidl': 'Lidl',
        'ikea': 'IKEA',
        'decathlon': 'Decathlon',
        'fnac': 'Fnac',
        'darty': 'Darty',
        'boulanger': 'Boulanger',
        'cdiscount': 'Cdiscount',
        'aliexpress': 'AliExpress',
        'paypal': 'PayPal',
        'stripe': 'Stripe',
        'ovh': 'OVH',
        'scaleway': 'Scaleway',
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'adobe': 'Adobe',
        'dropbox': 'Dropbox',
        'slack': 'Slack',
        'zoom': 'Zoom',
        'github': 'GitHub',
        'heroku': 'Heroku',
        'aws': 'AWS',
        'digitalocean': 'DigitalOcean',
    }
    
    def __init__(self, ocr_lang: str = 'eng+fra'):
        self.ocr_lang = ocr_lang
        self.min_score = 25  # Minimum score to be considered an invoice
    
    @staticmethod
    def get_downloads_folder() -> str:
        """Get the Downloads folder path based on the OS."""
        if platform.system() == 'Windows':
            return str(Path.home() / 'Downloads')
        elif platform.system() == 'Darwin':  # macOS
            return str(Path.home() / 'Downloads')
        else:  # Linux
            return str(Path.home() / 'Downloads')
    
    @staticmethod
    def get_invoices_folder() -> str:
        """Get the invoices destination folder."""
        return os.path.join(InvoiceDetector.get_downloads_folder(), 'factures')
    
    def get_file_type(self, file_path: str) -> FileType:
        """Determine file type from extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return FileType.PDF
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            return FileType.IMAGE
        elif ext in ['.docx', '.doc']:
            return FileType.WORD
        return FileType.UNKNOWN
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber or PyPDF2."""
        text = ""
        
        # Try pdfplumber first (better for structured PDFs)
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages[:5]:  # Limit to first 5 pages
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return text
            except Exception as e:
                print(f"pdfplumber error: {e}")
        
        # Fallback to PyPDF2
        if HAS_PYPDF2:
            try:
                reader = PdfReader(file_path)
                for page in reader.pages[:5]:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    return text
            except Exception as e:
                print(f"PyPDF2 error: {e}")
        
        # If no text extracted, try OCR on first page
        if HAS_OCR and HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(file_path) as pdf:
                    if pdf.pages:
                        # Convert first page to image
                        img = pdf.pages[0].to_image(resolution=200)
                        # OCR the image
                        text = pytesseract.image_to_string(img.original, lang=self.ocr_lang)
            except Exception as e:
                print(f"OCR on PDF error: {e}")
        
        return text
    
    def extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        if not HAS_OCR:
            return ""
        
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang=self.ocr_lang)
            return text.strip()
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word document."""
        if not HAS_DOCX:
            return ""
        
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"DOCX error: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extract text from any supported file type."""
        file_type = self.get_file_type(file_path)
        error = None
        text = ""
        
        try:
            if file_type == FileType.PDF:
                text = self.extract_text_from_pdf(file_path)
            elif file_type == FileType.IMAGE:
                text = self.extract_text_from_image(file_path)
            elif file_type == FileType.WORD:
                text = self.extract_text_from_docx(file_path)
            else:
                error = "Unsupported file type"
        except Exception as e:
            error = str(e)
        
        return text, error
    
    def calculate_invoice_score(self, text: str) -> Tuple[int, float, List[str]]:
        """Calculate score that document is an invoice.
        
        Returns:
            Tuple of (raw_score, confidence_percentage, detected_keywords)
        """
        if not text:
            return 0, 0.0, []
        
        text_lower = text.lower()
        total_score = 0
        detected_keywords = []
        
        for keyword, weight in self.INVOICE_KEYWORDS.items():
            if keyword in text_lower:
                total_score += weight
                detected_keywords.append(keyword)
        
        # Additional scoring for patterns
        # Currency amounts (€, $, EUR)
        if re.search(r'[\d\s,.]+\s*[€$]|EUR\s*[\d\s,.]+|[\d\s,.]+\s*EUR', text, re.IGNORECASE):
            total_score += 10
            detected_keywords.append('montant_€')
        
        # Invoice number pattern
        if re.search(r'(facture|invoice|fact|inv)[^\d]{0,10}(\d{4,})', text_lower):
            total_score += 10
            detected_keywords.append('n°_facture')
        
        # SIRET pattern (14 digits)
        if re.search(r'\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b', text):
            total_score += 8
            detected_keywords.append('siret')
        
        # Date patterns (common invoice dates)
        if re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', text):
            total_score += 5
            detected_keywords.append('date')
        
        # IBAN pattern
        if re.search(r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b', text):
            total_score += 8
            detected_keywords.append('iban')
        
        # Calculate confidence as percentage (50 points = 100% confident)
        confidence = min(total_score / 50.0, 1.0)
        
        return total_score, confidence, detected_keywords
    
    def extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from document text.
        
        Priority:
        1. User-defined companies from settings (highest priority)
        2. Built-in known companies
        3. Detection from legal entities, SIRET, etc.
        4. If nothing found, return None (will be "Inconnu")
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # 1. PRIORITY: Check user-defined companies from settings first
        user_companies = settings.get_invoice_companies()
        for company in user_companies:
            # Search for the company name (case insensitive)
            if company.lower() in text_lower:
                print(f"[DEBUG] Société trouvée (liste utilisateur): {company}")
                return company
        
        # 2. Check built-in known companies
        for key, name in self.KNOWN_COMPANIES.items():
            if key in text_lower:
                print(f"[DEBUG] Société trouvée (liste intégrée): {name}")
                return name
        
        # 3. If no predefined company found, return None -> will be "Inconnu"
        # We don't try to guess the company name anymore to avoid errors
        print(f"[DEBUG] Aucune société reconnue, sera classé dans 'Inconnu'")
        return None
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for folder creation."""
        if not name:
            return "Inconnu"
        
        # Remove legal suffixes
        for entity in self.LEGAL_ENTITIES:
            name = re.sub(rf'\s*{entity}\s*\.?\s*$', '', name, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove special characters not allowed in folder names
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        
        # Capitalize properly
        name = name.strip().title()
        
        # Limit length
        if len(name) > 50:
            name = name[:50]
        
        return name if name else "Inconnu"
    
    def analyze_file(self, file_path: str) -> InvoiceResult:
        """Analyze a single file to determine if it's an invoice."""
        file_name = os.path.basename(file_path)
        
        # Extract text
        text, error = self.extract_text(file_path)
        
        if error:
            return InvoiceResult(
                file_path=file_path,
                file_name=file_name,
                is_invoice=False,
                confidence_score=0.0,
                company_name=None,
                extracted_text="",
                detected_keywords=[],
                error=error
            )
        
        # Check if text was extracted
        if not text or len(text.strip()) < 10:
            return InvoiceResult(
                file_path=file_path,
                file_name=file_name,
                is_invoice=False,
                confidence_score=0.0,
                company_name=None,
                extracted_text="",
                detected_keywords=[],
                error="Aucun texte extrait du document"
            )
        
        # Calculate invoice score
        raw_score, confidence, keywords = self.calculate_invoice_score(text)
        is_invoice = raw_score >= self.min_score
        
        # Debug output
        print(f"[DEBUG] {file_name}: score={raw_score}, confidence={confidence:.0%}, keywords={keywords[:5]}")
        
        # Extract company name if it's an invoice
        company_name = None
        if is_invoice:
            company_name = self.extract_company_name(text)
            if not company_name:
                company_name = "Inconnu"
        
        return InvoiceResult(
            file_path=file_path,
            file_name=file_name,
            is_invoice=is_invoice,
            confidence_score=confidence,
            company_name=company_name,
            extracted_text=text[:500] if text else "",  # Preview only
            detected_keywords=keywords
        )
    
    def scan_downloads_folder(self) -> List[str]:
        """Scan downloads folder and return list of supported files."""
        downloads = self.get_downloads_folder()
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.docx'}
        files = []
        
        if not os.path.exists(downloads):
            return files
        
        for item in os.listdir(downloads):
            item_path = os.path.join(downloads, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item)[1].lower()
                if ext in supported_extensions:
                    files.append(item_path)
        
        return files
    
    def move_invoice(self, file_path: str, company_name: str) -> Tuple[bool, str]:
        """Move invoice to the appropriate folder."""
        try:
            invoices_folder = self.get_invoices_folder()
            company_folder = os.path.join(invoices_folder, company_name)
            
            # Create folders if needed
            os.makedirs(company_folder, exist_ok=True)
            
            # Handle duplicate filenames
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(company_folder, file_name)
            
            counter = 1
            base_name, ext = os.path.splitext(file_name)
            while os.path.exists(dest_path):
                dest_path = os.path.join(company_folder, f"{base_name}_{counter}{ext}")
                counter += 1
            
            # Move the file
            os.rename(file_path, dest_path)
            
            return True, dest_path
        except Exception as e:
            return False, str(e)

