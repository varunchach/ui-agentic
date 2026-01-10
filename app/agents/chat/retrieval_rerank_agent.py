"""Retrieval and re-ranking agent for chat flow."""

import logging
from typing import List, Tuple
from langchain_core.documents import Document

from app.ingestion.vector_store import FAISSVectorStore
from app.ingestion.embedder import NomicEmbedder
from app.utils.reranker import BGEReranker
from app.config.settings import config

logger = logging.getLogger(__name__)


class RetrievalRerankAgent:
    """Retrieves and re-ranks documents for chat Q&A."""
    
    def __init__(self, vector_store: FAISSVectorStore):
        """Initialize retrieval and re-ranking agent.
        
        Args:
            vector_store: FAISSVectorStore instance
        """
        self.vector_store = vector_store
        self.embedder = NomicEmbedder()
        self.reranker = BGEReranker()
    
    def retrieve_and_rerank(self, query: str) -> List[Tuple[Document, float]]:
        """Retrieve and re-rank documents for query.
        
        Args:
            query: User query (should be refined by QueryUnderstandingAgent)
            
        Returns:
            List of (Document, relevance_score) tuples, sorted by relevance
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_query(query)
            
            # Initial retrieval
            initial_results = self.vector_store.search(
                query_embedding,
                k=config.retrieval.top_k
            )
            
            if not initial_results:
                logger.warning("No results from initial retrieval")
                return []
            
            # Extract documents
            documents = [doc for doc, score in initial_results]
            
            # Re-rank for better relevance
            reranked_results = self.reranker.rerank(
                query=query,
                documents=documents,
                top_k=config.retrieval.rerank_top_k
            )
            
            logger.info(f"Retrieved and re-ranked {len(reranked_results)} documents")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error in retrieval and re-ranking: {str(e)}")
            return []
