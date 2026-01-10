"""BGE Large re-ranker implementation."""

import logging
from typing import List, Tuple, Optional
from langchain_core.documents import Document

from app.config.settings import config

logger = logging.getLogger(__name__)


class BGEReranker:
    """BGE Large re-ranker for improving retrieval quality."""
    
    def __init__(self):
        self.model_name = config.reranker.model
        self._model = None
        self._tokenizer = None
        logger.info(f"Initializing BGE re-ranker with model: {self.model_name}")
    
    def _load_model(self):
        """Lazy load the re-ranker model."""
        if self._model is None:
            try:
                from FlagEmbedding import FlagReranker
                import os
                
                # Optionally use Hugging Face token if available (for better rate limits)
                hf_token = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
                
                if hf_token:
                    # Set Hugging Face token for authentication
                    os.environ["HF_TOKEN"] = hf_token
                    logger.info("Using Hugging Face token for model download")
                
                self._model = FlagReranker(self.model_name, use_fp16=True)
                logger.info(f"Loaded BGE re-ranker model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "FlagEmbedding not installed. "
                    "Install with: pip install FlagEmbedding"
                )
            except Exception as e:
                logger.error(f"Error loading re-ranker model: {str(e)}")
                logger.info("Note: Hugging Face login is optional but recommended for better rate limits")
                raise
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """Re-rank documents based on query relevance.
        
        Args:
            query: Query text
            documents: List of Document objects to re-rank
            top_k: Number of top results to return (defaults to config value)
            
        Returns:
            List of (Document, relevance_score) tuples, sorted by relevance
        """
        if not documents:
            return []
        
        self._load_model()
        top_k = top_k or config.reranker.top_k
        
        try:
            # Prepare query-document pairs
            pairs = []
            for doc in documents:
                pairs.append([query, doc.page_content])
            
            # Get relevance scores
            scores = self._model.compute_score(pairs)
            
            # Handle single score vs list of scores
            if isinstance(scores, float):
                scores = [scores]
            elif not isinstance(scores, list):
                scores = list(scores)
            
            # Create document-score pairs
            doc_scores = list(zip(documents, scores))
            
            # Sort by score (descending)
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k
            results = doc_scores[:top_k]
            
            logger.debug(f"Re-ranked {len(documents)} documents, returning top {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Error during re-ranking: {str(e)}")
            # Fallback: return original documents with dummy scores
            return [(doc, 0.0) for doc in documents[:top_k]]
