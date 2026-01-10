"""Embedding generation using nomic-ai from Hugging Face."""

import logging
from typing import List
import numpy as np
from langchain_core.documents import Document
import os
from app.config.settings import config

logger = logging.getLogger(__name__)


class NomicEmbedder:
    """Generate embeddings using nomic-ai models from Hugging Face."""
    
    def __init__(self):
        # Use configured embedding model
        self.model_name = config.embedding.model
        self.hf_model_name = self.model_name
        self.dimension = config.embedding.dimension
        self._model = None
        logger.info(f"Initializing embedder with model: {self.hf_model_name}")
    
    def _get_model(self):
        """Lazy load the embedding model from Hugging Face."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                
                # Optionally use Hugging Face token if available
                hf_token = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
                
                if hf_token:
                    # Set token for authentication
                    os.environ["HF_TOKEN"] = hf_token
                    logger.info("Using Hugging Face token for model download")
                
                # Load model - only use trust_remote_code for models that need it (like nomic)
                needs_trust_remote_code = "nomic" in self.hf_model_name.lower()
                self._model = SentenceTransformer(
                    self.hf_model_name,
                    trust_remote_code=needs_trust_remote_code,
                    token=hf_token if hf_token else None
                )
                logger.info(f"Loaded embedding model: {self.hf_model_name}")
                        
            except ImportError as e:
                import sys
                error_str = str(e)
                # Check if it's a missing dependency issue
                if "einops" in error_str.lower():
                    install_cmd = "pip install einops"
                elif "sentence-transformers" in error_str.lower():
                    install_cmd = "pip install sentence-transformers"
                else:
                    install_cmd = "pip install sentence-transformers einops"
                
                error_msg = (
                    f"Missing dependency for embedding model.\n"
                    f"Python executable: {sys.executable}\n"
                    f"Original error: {error_str}\n"
                    f"Install with: {install_cmd}\n"
                    f"Or activate venv and run: source venv/bin/activate && {install_cmd}"
                )
                logger.error(error_msg)
                raise ImportError(error_msg) from e
            except Exception as e:
                logger.error(f"Error loading embedding model: {str(e)}")
                raise
        return self._model
    
    def embed_documents(self, documents: List[Document], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of documents.
        
        Args:
            documents: List of Document objects
            batch_size: Batch size for embedding generation
            
        Returns:
            numpy array of embeddings with shape (n_documents, embedding_dim)
        """
        texts = [doc.page_content for doc in documents]
        
        try:
            model = self._get_model()
            
            # Generate embeddings using sentence-transformers
            # The model.encode() method handles batching automatically
            embeddings_array = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            
            # Ensure float32 dtype
            embeddings_array = np.array(embeddings_array, dtype=np.float32)
            
            logger.info(f"Generated embeddings for {len(documents)} documents: shape {embeddings_array.shape}")
            
            return embeddings_array
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query.
        
        Args:
            query: Query text
            
        Returns:
            numpy array of embedding with shape (embedding_dim,)
        """
        try:
            model = self._get_model()
            
            # Generate embedding using sentence-transformers
            embedding = model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            
            # Ensure float32 dtype and 1D array
            embedding = np.array(embedding, dtype=np.float32).flatten()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
