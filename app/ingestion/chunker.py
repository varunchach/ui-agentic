"""Section-aware document chunking with overlap."""

import logging
import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import config

logger = logging.getLogger(__name__)


class SectionAwareChunker:
    """Chunk documents with section awareness and overlap."""
    
    def __init__(self):
        self.chunk_size = config.chunking.chunk_size
        self.chunk_overlap = config.chunking.chunk_overlap
        self.section_aware = config.chunking.section_aware
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def chunk(self, documents: List[Document]) -> List[Document]:
        """Chunk documents with section awareness.
        
        Args:
            documents: List of Document objects to chunk
            
        Returns:
            List of chunked Document objects with enriched metadata
        """
        chunked_docs = []
        
        for doc_idx, doc in enumerate(documents):
            text = doc.page_content
            metadata = doc.metadata.copy()
            
            if self.section_aware:
                # Detect sections and preserve structure
                sections = self._detect_sections(text)
                chunks = self._chunk_with_sections(text, sections, metadata)
            else:
                # Simple chunking without section awareness
                chunks = self._simple_chunk(text, metadata)
            
            # Add chunk metadata
            for chunk_idx, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = f"{doc_idx}_{chunk_idx}"
                chunk.metadata["chunk_index"] = chunk_idx
                chunk.metadata["total_chunks"] = len(chunks)
                chunk.metadata["document_index"] = doc_idx
                
                # Preserve original metadata
                for key, value in metadata.items():
                    if key not in chunk.metadata:
                        chunk.metadata[key] = value
            
            chunked_docs.extend(chunks)
        
        logger.info(f"Chunked {len(documents)} documents into {len(chunked_docs)} chunks")
        return chunked_docs
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Detect document sections based on headers and patterns.
        
        Returns:
            List of section dictionaries with start, end, and title
        """
        sections = []
        
        # Pattern for section headers (numbered, bulleted, or bold text)
        section_patterns = [
            r"^\d+\.\s+[A-Z][^\n]+",  # Numbered sections: "1. Section Title"
            r"^[A-Z][A-Z\s]{5,}$",  # ALL CAPS headers
            r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:",  # Title Case: "Section Title:"
            r"^#{1,3}\s+.+",  # Markdown headers
        ]
        
        lines = text.split("\n")
        current_section = {"title": "Introduction", "start": 0, "end": 0}
        
        for i, line in enumerate(lines):
            for pattern in section_patterns:
                if re.match(pattern, line.strip()):
                    # End previous section
                    if current_section["end"] > 0:
                        current_section["end"] = i
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        "title": line.strip(),
                        "start": i,
                        "end": len(lines) - 1,
                    }
                    break
        
        # Add final section
        if current_section["end"] == 0:
            current_section["end"] = len(lines) - 1
        sections.append(current_section)
        
        return sections if sections else [{"title": "Document", "start": 0, "end": len(lines) - 1}]
    
    def _chunk_with_sections(self, text: str, sections: List[Dict[str, Any]], base_metadata: Dict) -> List[Document]:
        """Chunk text while preserving section boundaries."""
        chunks = []
        lines = text.split("\n")
        
        for section in sections:
            section_text = "\n".join(lines[section["start"]:section["end"] + 1])
            
            # Chunk within section
            section_chunks = self.text_splitter.split_text(section_text)
            
            for chunk_text in section_chunks:
                chunk_metadata = base_metadata.copy()
                chunk_metadata["section"] = section["title"]
                chunk_metadata["section_start"] = section["start"]
                chunk_metadata["section_end"] = section["end"]
                
                chunks.append(Document(page_content=chunk_text, metadata=chunk_metadata))
        
        return chunks
    
    def _simple_chunk(self, text: str, base_metadata: Dict) -> List[Document]:
        """Simple chunking without section awareness."""
        chunk_texts = self.text_splitter.split_text(text)
        
        chunks = []
        for chunk_text in chunk_texts:
            chunk_metadata = base_metadata.copy()
            chunks.append(Document(page_content=chunk_text, metadata=chunk_metadata))
        
        return chunks
