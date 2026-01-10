"""Document loading utilities using LangChain and Docling."""

import logging
from pathlib import Path
from typing import List, Optional
from io import BytesIO

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Load documents from various formats."""
    
    def __init__(self):
        self.supported_extensions = {".pdf", ".txt", ".docx", ".doc"}
    
    def load(self, file_path: str, file_content: Optional[bytes] = None) -> List[Document]:
        """Load document from file path or file content.
        
        Args:
            file_path: Path to the document file
            file_content: Optional file content as bytes (for Streamlit uploads)
            
        Returns:
            List of Document objects with metadata
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {extension}")
        
        try:
            if file_content:
                # Handle in-memory file content (from Streamlit upload)
                return self._load_from_bytes(file_content, extension, file_path)
            else:
                # Load from file system
                return self._load_from_path(path, extension)
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def _load_from_path(self, path: Path, extension: str) -> List[Document]:
        """Load document from file path."""
        if extension == ".pdf":
            loader = PyPDFLoader(str(path))
        elif extension == ".txt":
            loader = TextLoader(str(path), encoding="utf-8")
        elif extension in {".docx", ".doc"}:
            loader = UnstructuredWordDocumentLoader(str(path))
        else:
            raise ValueError(f"Unsupported extension: {extension}")
        
        documents = loader.load()
        
        # Enrich metadata
        for doc in documents:
            doc.metadata["source_file"] = str(path)
            doc.metadata["file_type"] = extension[1:]  # Remove dot
            if "page" not in doc.metadata:
                doc.metadata["page"] = 0
        
        logger.info(f"Loaded {len(documents)} document chunks from {path}")
        return documents
    
    def _load_from_bytes(self, content: bytes, extension: str, file_path: str) -> List[Document]:
        """Load document from bytes (for Streamlit uploads)."""
        import tempfile
        import os
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Load using path-based loader
            documents = self._load_from_path(Path(tmp_path), extension)
            
            # Update source metadata to original filename
            for doc in documents:
                doc.metadata["source_file"] = file_path
                doc.metadata["is_uploaded"] = True
            
            return documents
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported."""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_extensions
