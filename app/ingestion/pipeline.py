"""Document ingestion pipeline orchestration."""

import logging
from pathlib import Path
from typing import List, Optional, Callable
from langchain_core.documents import Document

from app.ingestion.document_loader import DocumentLoader
from app.ingestion.chunker import SectionAwareChunker
from app.ingestion.embedder import NomicEmbedder
from app.ingestion.vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrate the complete document ingestion pipeline."""
    
    def __init__(self, progress_callback: Optional[Callable[[str, float], None]] = None):
        """Initialize ingestion pipeline.
        
        Args:
            progress_callback: Optional callback function(step_name, progress) for UI updates
        """
        self.loader = DocumentLoader()
        self.chunker = SectionAwareChunker()
        self.embedder = NomicEmbedder()
        # Initialize vector store with correct dimension from embedder
        self.vector_store = FAISSVectorStore(dimension=self.embedder.dimension)
        self.progress_callback = progress_callback
    
    def ingest(
        self,
        file_path: str,
        file_content: Optional[bytes] = None,
        document_id: Optional[str] = None
    ) -> FAISSVectorStore:
        """Run complete ingestion pipeline.
        
        Args:
            file_path: Path to document or filename
            file_content: Optional file content as bytes (for Streamlit uploads)
            document_id: Optional unique document identifier
            
        Returns:
            FAISSVectorStore instance with indexed documents
        """
        try:
            # Step 1: Load document
            self._update_progress("Loading document...", 0.1)
            documents = self.loader.load(file_path, file_content)
            
            if not documents:
                raise ValueError("No documents loaded from file")
            
            logger.info(f"Loaded {len(documents)} document chunks")
            
            # Step 2: Chunk documents
            self._update_progress("Chunking document...", 0.3)
            chunked_documents = self.chunker.chunk(documents)
            
            if not chunked_documents:
                raise ValueError("No chunks created from documents")
            
            logger.info(f"Created {len(chunked_documents)} chunks")
            
            # Step 3: Generate embeddings
            self._update_progress("Generating embeddings...", 0.5)
            embeddings = self.embedder.embed_documents(chunked_documents)
            
            logger.info(f"Generated {embeddings.shape[0]} embeddings")
            
            # Step 4: Create vector store
            self._update_progress("Creating vector index...", 0.8)
            self.vector_store.clear()
            self.vector_store.add_documents(chunked_documents, embeddings)
            
            # Step 5: Save to disk
            self._update_progress("Saving vector store...", 0.9)
            doc_id = document_id or Path(file_path).stem
            self.vector_store.save(file_prefix=doc_id)
            
            self._update_progress("Ingestion complete!", 1.0)
            logger.info(f"Ingestion complete: {len(chunked_documents)} chunks indexed")
            
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Ingestion pipeline error: {str(e)}")
            self._update_progress(f"Error: {str(e)}", 0.0)
            raise
    
    def load_existing(self, document_id: str) -> FAISSVectorStore:
        """Load existing vector store for a document.
        
        Args:
            document_id: Document identifier used during ingestion
            
        Returns:
            FAISSVectorStore instance
        """
        try:
            self.vector_store.load(file_prefix=document_id)
            logger.info(f"Loaded existing vector store for document: {document_id}")
            return self.vector_store
        except FileNotFoundError:
            logger.warning(f"Vector store not found for document: {document_id}")
            raise
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise
    
    def _update_progress(self, message: str, progress: float):
        """Update progress callback if available."""
        if self.progress_callback:
            self.progress_callback(message, progress)
        logger.debug(f"{message} ({progress:.1%})")
