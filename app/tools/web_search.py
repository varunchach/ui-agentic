"""Web search tool using Tavily, DuckDuckGo, or SerpAPI."""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web search tool for real-time information retrieval."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "tavily"):
        """Initialize web search tool.
        
        Args:
            api_key: API key for Tavily or SerpAPI
            provider: Search provider ('tavily', 'duckduckgo', or 'serpapi')
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self._search_engine = None
    
    def _get_search_engine(self):
        """Lazy load search engine."""
        if self._search_engine is None:
            if self.provider == "tavily":
                if not self.api_key:
                    raise ValueError("Tavily API key is required. Get one from https://tavily.com/")
                try:
                    from tavily import TavilyClient
                    self._search_engine = TavilyClient(api_key=self.api_key)
                    logger.info("Using Tavily for web search")
                except ImportError:
                    raise ImportError(
                        "tavily-python not installed. "
                        "Install with: pip install tavily-python"
                    )
            elif self.provider == "serpapi" and self.api_key:
                try:
                    from serpapi import GoogleSearch
                    self._search_engine = GoogleSearch
                    logger.info("Using SerpAPI for web search")
                except ImportError:
                    logger.warning("serpapi not installed, falling back to DuckDuckGo")
                    self.provider = "duckduckgo"
            
            if self.provider == "duckduckgo":
                try:
                    from duckduckgo_search import DDGS
                    self._search_engine = DDGS()
                    logger.info("Using DuckDuckGo for web search")
                except ImportError:
                    raise ImportError(
                        "duckduckgo-search not installed. "
                        "Install with: pip install duckduckgo-search"
                    )
        
        return self._search_engine
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and url
        """
        try:
            engine = self._get_search_engine()
            
            if self.provider == "tavily":
                # Tavily is optimized for RAG - returns clean, relevant results
                response = engine.search(
                    query=query,
                    search_depth="advanced",  # Options: "basic" or "advanced"
                    max_results=max_results,
                    include_answer=True,  # Get AI-generated answer
                    include_raw_content=False
                )
                
                results = []
                
                # Add AI-generated answer if available
                if response.get("answer"):
                    results.append({
                        "title": "AI Summary",
                        "snippet": response["answer"],
                        "url": "",
                        "is_answer": True
                    })
                
                # Add search results
                for result in response.get("results", [])[:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("content", ""),
                        "url": result.get("url", "")
                    })
                
                return results
                
            elif self.provider == "serpapi":
                search = engine({"q": query, "api_key": self.api_key})
                results = []
                for result in search.get("organic_results", [])[:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", "")
                    })
                return results
            else:  # duckduckgo
                results = []
                for result in engine.text(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", "")
                    })
                return results
                
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            return []
    
    def __call__(self, query: str) -> str:
        """Make tool callable.
        
        Args:
            query: Search query
            
        Returns:
            Formatted search results as string
        """
        results = self.search(query)
        if not results:
            return "No search results found."
        
        formatted = "Web Search Results:\n\n"
        
        # Check if first result is AI answer (Tavily)
        if results and results[0].get("is_answer"):
            formatted += f"**AI Summary:**\n{results[0]['snippet']}\n\n"
            formatted += "**Sources:**\n"
            results = results[1:]  # Skip the answer, show sources
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   {result['snippet'][:300]}...\n"  # Limit snippet length
            if result.get('url'):
                formatted += f"   Source: {result['url']}\n"
            formatted += "\n"
        
        return formatted
