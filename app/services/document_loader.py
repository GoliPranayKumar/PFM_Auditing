"""Document processing and text extraction service."""

import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
import shutil

# LangChain document loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)

# PDF processing
from PyPDF2 import PdfReader

# DOCX processing
from docx import Document as DocxDocument


class DocumentLoaderService:
    """Service for loading and extracting text from various document formats."""
    
    # Supported file types
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
    
    # Uploads directory
    UPLOADS_DIR = Path("uploads")
    
    def __init__(self):
        """Initialize the document loader service."""
        # Create uploads directory if it doesn't exist
        self.UPLOADS_DIR.mkdir(exist_ok=True)
        
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Args:
            filename: Name of the uploaded file
            file_size: Size of the file in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
        
        # Check file size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            max_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
    
    def save_upload(self, file_content: bytes, filename: str) -> Path:
        """
        Save uploaded file temporarily.
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(filename).stem  # Remove extension
        file_ext = Path(filename).suffix
        unique_filename = f"{safe_filename}_{timestamp}{file_ext}"
        
        filepath = self.UPLOADS_DIR / unique_filename
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        return filepath
    
    def extract_text_from_pdf(self, filepath: Path) -> str:
        """
        Extract text from PDF file using PyPDF2.
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text_parts = []
        
        try:
            # Try PyPDF2 first (faster)
            reader = PdfReader(str(filepath))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        except Exception as e:
            # Fallback to LangChain loader
            try:
                loader = PyPDFLoader(str(filepath))
                documents = loader.load()
                text_parts = [doc.page_content for doc in documents]
            except Exception as fallback_error:
                raise Exception(f"Failed to extract PDF text: {fallback_error}")
        
        return "\n\n".join(text_parts)
    
    def extract_text_from_docx(self, filepath: Path) -> str:
        """
        Extract text from DOCX file using python-docx.
        
        Args:
            filepath: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            # Try python-docx first
            doc = DocxDocument(str(filepath))
            text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            return "\n\n".join(text_parts)
        except Exception as e:
            # Fallback to LangChain loader
            try:
                loader = Docx2txtLoader(str(filepath))
                documents = loader.load()
                return "\n\n".join([doc.page_content for doc in documents])
            except Exception as fallback_error:
                raise Exception(f"Failed to extract DOCX text: {fallback_error}")
    
    def extract_text_from_txt(self, filepath: Path) -> str:
        """
        Extract text from TXT file.
        
        Args:
            filepath: Path to TXT file
            
        Returns:
            Extracted text content
        """
        try:
            # Try UTF-8 encoding first
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # Fallback to LangChain loader
            try:
                loader = TextLoader(str(filepath), encoding='utf-8', autodetect_encoding=True)
                documents = loader.load()
                return "\n\n".join([doc.page_content for doc in documents])
            except Exception as fallback_error:
                raise Exception(f"Failed to extract TXT text: {fallback_error}")
    
    def extract_text(self, filepath: Path) -> str:
        """
        Extract text from document based on file type.
        
        Args:
            filepath: Path to document file
            
        Returns:
            Extracted and normalized text
            
        Raises:
            ValueError: If file type is unsupported
            Exception: If text extraction fails
        """
        file_ext = filepath.suffix.lower()
        
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(filepath)
        elif file_ext == '.docx':
            text = self.extract_text_from_docx(filepath)
        elif file_ext == '.txt':
            text = self.extract_text_from_txt(filepath)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Normalize text
        text = self.normalize_text(text)
        
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join with single newlines
        normalized = '\n'.join(lines)
        
        # Remove multiple consecutive spaces
        import re
        normalized = re.sub(r' +', ' ', normalized)
        
        return normalized.strip()
    
    def cleanup_file(self, filepath: Path) -> None:
        """
        Delete temporary file.
        
        Args:
            filepath: Path to file to delete
        """
        try:
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            # Log but don't raise - cleanup failures shouldn't break the flow
            print(f"Warning: Failed to cleanup file {filepath}: {e}")
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old uploaded files.
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        if not self.UPLOADS_DIR.exists():
            return 0
        
        deleted = 0
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        for filepath in self.UPLOADS_DIR.iterdir():
            if filepath.is_file():
                file_age = current_time - filepath.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        filepath.unlink()
                        deleted += 1
                    except Exception:
                        pass
        
        return deleted
    
    def process_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        cleanup_after: bool = True
    ) -> Tuple[str, dict]:
        """
        Complete workflow: validate, save, extract, cleanup.
        
        Args:
            file_content: Binary content of uploaded file
            filename: Original filename
            cleanup_after: Whether to delete file after extraction
            
        Returns:
            Tuple of (extracted_text, metadata)
            
        Raises:
            ValueError: If validation fails
            Exception: If extraction fails
        """
        # Validate
        is_valid, error = self.validate_file(filename, len(file_content))
        if not is_valid:
            raise ValueError(error)
        
        filepath = None
        try:
            # Save file
            filepath = self.save_upload(file_content, filename)
            
            # Extract text
            extracted_text = self.extract_text(filepath)
            
            # Create metadata
            metadata = {
                "original_filename": filename,
                "file_type": filepath.suffix.lower(),
                "file_size_bytes": len(file_content),
                "extracted_length": len(extracted_text),
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            return extracted_text, metadata
            
        finally:
            # Cleanup if requested
            if cleanup_after and filepath:
                self.cleanup_file(filepath)


# Global service instance
document_loader_service = DocumentLoaderService()
