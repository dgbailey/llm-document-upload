import os
import PyPDF2
import docx
from PIL import Image
from typing import Optional, Tuple
from .models import DocumentType
from .config import settings

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str, document_type: DocumentType) -> Tuple[str, int]:
        """Extract text from document and return (text, page_count)"""
        
        # In demo mode, return simulated text
        if settings.demo_mode and not os.path.exists(file_path):
            return DocumentProcessor._get_demo_text(document_type)
        
        if document_type == DocumentType.PDF:
            return DocumentProcessor._extract_pdf(file_path)
        elif document_type == DocumentType.DOCX:
            return DocumentProcessor._extract_docx(file_path)
        elif document_type == DocumentType.TXT:
            return DocumentProcessor._extract_txt(file_path)
        elif document_type == DocumentType.IMAGE:
            return DocumentProcessor._extract_image(file_path)
        else:
            # Try to detect and extract
            return DocumentProcessor._auto_extract(file_path)
    
    @staticmethod
    def _get_demo_text(document_type: DocumentType) -> Tuple[str, int]:
        """Return demo text for different document types"""
        demo_texts = {
            DocumentType.PDF: ("This is a demo PDF document containing important information about project management, "
                              "financial reports, and strategic planning for the upcoming quarter. "
                              "The document includes detailed analysis of market trends, competitive landscape, "
                              "and recommendations for future growth strategies.", 5),
            DocumentType.DOCX: ("This is a demo Word document with meeting notes from the quarterly review. "
                               "Key topics discussed include product roadmap updates, team performance metrics, "
                               "and budget allocations for the next fiscal year.", 3),
            DocumentType.TXT: ("This is a demo text file containing technical documentation and API specifications. "
                              "It covers authentication methods, endpoint descriptions, and usage examples.", 2),
            DocumentType.IMAGE: ("This appears to be an image document. In demo mode, we simulate that this image "
                                "contains a chart showing quarterly revenue growth and key performance indicators.", 1),
            DocumentType.UNKNOWN: ("This is a demo document of unknown type. The content appears to be related to "
                                  "business operations and includes various data points and analysis.", 1)
        }
        return demo_texts.get(document_type, demo_texts[DocumentType.UNKNOWN])
    
    @staticmethod
    def _extract_pdf(file_path: str) -> Tuple[str, int]:
        text = ""
        page_count = 0
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num in range(page_count):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
        except Exception as e:
            if settings.demo_mode:
                return DocumentProcessor._get_demo_text(DocumentType.PDF)
            raise Exception(f"Failed to extract PDF: {str(e)}")
        
        return text.strip(), page_count
    
    @staticmethod
    def _extract_docx(file_path: str) -> Tuple[str, int]:
        text = ""
        page_count = 1  # Approximate
        
        try:
            doc = docx.Document(file_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            text = "\n".join(paragraphs)
            # Rough page estimation (assuming ~500 words per page)
            word_count = len(text.split())
            page_count = max(1, word_count // 500)
        except Exception as e:
            if settings.demo_mode:
                return DocumentProcessor._get_demo_text(DocumentType.DOCX)
            raise Exception(f"Failed to extract DOCX: {str(e)}")
        
        return text.strip(), page_count
    
    @staticmethod
    def _extract_txt(file_path: str) -> Tuple[str, int]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # Rough page estimation
            word_count = len(text.split())
            page_count = max(1, word_count // 500)
            
            return text.strip(), page_count
        except Exception as e:
            if settings.demo_mode:
                return DocumentProcessor._get_demo_text(DocumentType.TXT)
            raise Exception(f"Failed to extract TXT: {str(e)}")
    
    @staticmethod
    def _extract_image(file_path: str) -> Tuple[str, int]:
        try:
            # Try OCR using pytesseract if available
            import pytesseract
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip(), 1
        except:
            # If OCR fails or is not available, return demo text in demo mode
            if settings.demo_mode:
                return DocumentProcessor._get_demo_text(DocumentType.IMAGE)
            return "", 1
    
    @staticmethod
    def _auto_extract(file_path: str) -> Tuple[str, int]:
        # Try to detect file type by extension
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return DocumentProcessor._extract_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return DocumentProcessor._extract_docx(file_path)
        elif ext in ['.txt', '.text']:
            return DocumentProcessor._extract_txt(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return DocumentProcessor._extract_image(file_path)
        else:
            # Default to text extraction or demo
            if settings.demo_mode:
                return DocumentProcessor._get_demo_text(DocumentType.UNKNOWN)
            return DocumentProcessor._extract_txt(file_path)
    
    @staticmethod
    def detect_document_type(filename: str) -> DocumentType:
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            return DocumentType.PDF
        elif ext in ['.docx', '.doc']:
            return DocumentType.DOCX
        elif ext in ['.txt', '.text']:
            return DocumentType.TXT
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return DocumentType.IMAGE
        else:
            return DocumentType.UNKNOWN