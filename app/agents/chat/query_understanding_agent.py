"""Query understanding agent for chat flow."""

import logging
from langchain_core.prompts import ChatPromptTemplate

from app.config.settings import config

logger = logging.getLogger(__name__)


class QueryUnderstandingAgent:
    """Analyzes and refines user queries for better retrieval."""
    
    def __init__(self):
        """Initialize query understanding agent."""
        self.llm = self._get_llm()
    
    def _get_llm(self):
        """Get LLM instance based on configuration."""
        provider = config.llm.provider
        
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.llm.model,
                temperature=config.llm.temperature,
                api_key=config.llm.api_key
            )
        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=config.llm.model,
                    temperature=config.llm.temperature,
                    api_key=config.llm.api_key
                )
            except ImportError:
                raise ImportError("langchain-anthropic not installed. Install with: pip install langchain-anthropic")
        elif provider == "azure":
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                deployment_name=config.llm.deployment_name,
                model=config.llm.model,
                temperature=config.llm.temperature,
                api_key=config.llm.api_key,
                azure_endpoint=config.llm.endpoint,
                api_version=config.llm.api_version
            )
        elif provider == "custom":
            from langchain_openai import ChatOpenAI
            from app.utils.llm_optimizations import apply_llm_optimizations
            
            llm = ChatOpenAI(
                model=config.llm.model,
                temperature=config.llm.temperature,
                base_url=config.llm.endpoint,
                api_key=config.llm.api_key or "dummy"
            )
            
            # Apply optimizations (KV-caching, speculative decoding)
            return apply_llm_optimizations(llm)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def understand_query(self, query: str) -> str:
        """Analyze and refine query for better retrieval.
        
        Args:
            query: Original user query
            
        Returns:
            Refined query optimized for document retrieval
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a query understanding system for BFSI document analysis.

Your task is to analyze the user's query and refine it to improve document retrieval. The refined query should:
1. Extract key financial terms, metrics, and concepts
2. Expand abbreviations (e.g., ROE -> Return on Equity)
3. Include relevant synonyms and related terms
4. Maintain the original intent
5. Be optimized for semantic search in financial documents

Return ONLY the refined query, nothing else."""),
                ("human", "Original query: {query}\n\nRefined query:")
            ])
            
            formatted_prompt = prompt.format_messages(query=query)
            response = self.llm.invoke(formatted_prompt)
            
            if hasattr(response, 'content'):
                refined_query = response.content.strip()
            else:
                refined_query = str(response).strip()
            
            # Fallback to original if refinement is too short or empty
            if len(refined_query) < len(query) * 0.5:
                logger.warning("Refined query too short, using original")
                return query
            
            logger.debug(f"Query refined: '{query}' -> '{refined_query}'")
            return refined_query
            
        except Exception as e:
            logger.warning(f"Error in query understanding, using original: {str(e)}")
            return query
