"""FAISS vector store implementation."""

import logging
import pickle
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import faiss
from langchain_core.documents import Document

from app.config.settings import config

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for document embeddings."""
    
    def __init__(self, dimension: Optional[int] = None):
        """Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension (defaults to config value)
        """
        self.dimension = dimension or config.embedding.dimension
        self.index_path = config.vector_store.index_path
        self.store_path = config.vector_store.store_path
        self.index: Optional[faiss.Index] = None
        self.documents: List[Document] = []
        
        # Create directories
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
    
    def create_index(self, embeddings: np.ndarray):
        """Create FAISS index from embeddings.
        
        Args:
            embeddings: numpy array of embeddings with shape (n_documents, dimension)
        """
        if embeddings.shape[1] != self.dimension:
            # Update dimension to match actual embeddings
            logger.warning(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embeddings.shape[1]}. Updating dimension."
            )
            self.dimension = embeddings.shape[1]
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index (Inner Product for cosine similarity)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"Created FAISS index with {self.index.ntotal} vectors")
    
    def add_documents(self, documents: List[Document], embeddings: np.ndarray):
        """Add documents and their embeddings to the store.
        
        Args:
            documents: List of Document objects
            embeddings: numpy array of embeddings
        """
        if len(documents) != embeddings.shape[0]:
            raise ValueError(
                f"Document count mismatch: {len(documents)} documents, "
                f"{embeddings.shape[0]} embeddings"
            )
        
        if self.index is None:
            self.create_index(embeddings)
        else:
            # Normalize new embeddings
            normalized_embeddings = embeddings.astype('float32')
            faiss.normalize_L2(normalized_embeddings)
            self.index.add(normalized_embeddings)
        
        self.documents.extend(documents)
        logger.info(f"Added {len(documents)} documents. Total: {len(self.documents)}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_metadata: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of (Document, similarity_score) tuples
        """
        if self.index is None or len(self.documents) == 0:
            logger.warning("Index is empty, returning empty results")
            return []
        
        # Normalize query embedding
        query_vector = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Search
        k = min(k, self.index.ntotal)
        similarities, indices = self.index.search(query_vector, k)
        
        # Get documents and scores
        results = []
        for idx, score in zip(indices[0], similarities[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                
                # Apply metadata filter if provided
                if filter_metadata:
                    if all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                        results.append((doc, float(score)))
                else:
                    results.append((doc, float(score)))
        
        return results
    
    def save(self, file_prefix: Optional[str] = None):
        """Save index and documents to disk.
        
        Args:
            file_prefix: Optional prefix for saved files
        """
        if self.index is None:
            raise ValueError("No index to save")
        
        prefix = file_prefix or self.index_path.stem
        index_file = self.index_path.parent / f"{prefix}.faiss"
        docs_file = self.index_path.parent / f"{prefix}.pkl"
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_file))
        
        # Save documents
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"Saved vector store to {index_file} and {docs_file}")
    
    def load(self, file_prefix: Optional[str] = None):
        """Load index and documents from disk.
        
        Args:
            file_prefix: Optional prefix for saved files
        """
        prefix = file_prefix or self.index_path.stem
        index_file = self.index_path.parent / f"{prefix}.faiss"
        docs_file = self.index_path.parent / f"{prefix}.pkl"
        
        if not index_file.exists() or not docs_file.exists():
            raise FileNotFoundError(f"Vector store files not found: {index_file}, {docs_file}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_file))
        
        # Load documents
        with open(docs_file, 'rb') as f:
            self.documents = pickle.load(f)
        
        logger.info(f"Loaded vector store: {len(self.documents)} documents, {self.index.ntotal} vectors")
    
    def clear(self):
        """Clear the vector store."""
        self.index = None
        self.documents = []
        logger.info("Cleared vector store")
    
    def get_document_count(self) -> int:
        """Get the number of documents in the store."""
        return len(self.documents)
