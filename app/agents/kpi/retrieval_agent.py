"""Retrieval agent for KPI report flow."""

import logging
from typing import List, Tuple, Optional
from langchain_core.documents import Document

from app.ingestion.vector_store import FAISSVectorStore
from app.ingestion.embedder import NomicEmbedder
from app.utils.reranker import BGEReranker
from app.config.settings import config

logger = logging.getLogger(__name__)


class RetrievalAgent:
    """Retrieves relevant chunks for KPI extraction."""
    
    def __init__(self, vector_store: FAISSVectorStore):
        """Initialize retrieval agent.
        
        Args:
            vector_store: FAISSVectorStore instance
        """
        self.vector_store = vector_store
        self.embedder = NomicEmbedder()
        self.reranker = BGEReranker()
    
    def retrieve(self, query: Optional[str] = None) -> List[Document]:
        """Retrieve relevant chunks for KPI extraction.
        
        Args:
            query: Optional specific query (defaults to KPI-focused query)
            
        Returns:
            List of relevant Document objects
        """
        # Default query for KPI extraction
        if query is None:
            query = (
                "financial metrics revenue profit ROE ROA GNPA NNPA PCR CRAR CAR "
                "quarterly results annual report growth percentage"
            )
        
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
            
            # Return top re-ranked documents
            final_documents = [doc for doc, score in reranked_results]
            
            logger.info(f"Retrieved {len(final_documents)} relevant chunks after re-ranking")
            return final_documents
            
        except Exception as e:
            logger.error(f"Error in retrieval: {str(e)}")
            raise
