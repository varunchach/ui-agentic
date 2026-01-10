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
                    logger.warning("Tavily API key not provided, falling back to DuckDuckGo")
                    self.provider = "duckduckgo"
                else:
                    try:
                        from tavily import TavilyClient
                        self._search_engine = TavilyClient(api_key=self.api_key)
                        logger.info("Using Tavily for web search")
                        return self._search_engine
                    except ImportError:
                        logger.warning("tavily-python not installed, falling back to DuckDuckGo")
                        self.provider = "duckduckgo"
            
            if self.provider == "serpapi" and self.api_key:
                try:
                    from serpapi import GoogleSearch
                    self._search_engine = GoogleSearch
                    logger.info("Using SerpAPI for web search")
                    return self._search_engine
                except ImportError:
                    logger.warning("serpapi not installed, falling back to DuckDuckGo")
                    self.provider = "duckduckgo"
            
            if self.provider == "duckduckgo":
                try:
                    from duckduckgo_search import DDGS
                    self._search_engine = DDGS()
                    logger.info("Using DuckDuckGo for web search")
                    return self._search_engine
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
            # Validate query
            if not query or not query.strip():
                logger.error("Empty query provided to web search")
                return []
            
            engine = self._get_search_engine()
            
            if engine is None:
                logger.error("Search engine not initialized")
                return []
            
            if self.provider == "tavily":
                # Tavily search - query must be first positional argument
                logger.debug(f"Searching Tavily with query: '{query[:50]}...' (truncated)")
                # Use include_answer for better results, and include_raw_content for snippets
                response = engine.search(
                    query, 
                    max_results=max_results,
                    include_answer=True,  # Get AI-generated answer
                    include_raw_content="text",  # Include text content
                    search_depth="advanced"  # Better quality results
                )
                
                results = []
                
                # First, try to use the answer if available (Tavily's AI summary)
                answer = response.get("answer")
                if answer:
                    results.append({
                        "title": f"Summary for: {query}",
                        "snippet": self._clean_content(answer),
                        "url": "",
                        "is_answer": True
                    })
                
                # Then add individual results
                for result in response.get("results", [])[:max_results]:
                    title = result.get("title", "").strip()
                    content = result.get("content", "") or result.get("raw_content", "") or ""
                    url = result.get("url", "").strip()
                    
                    # Filter out low-quality results
                    if not title or not content:
                        continue
                    
                    # Clean and truncate content
                    cleaned_content = self._clean_content(content)
                    if not cleaned_content:
                        continue
                    
                    results.append({
                        "title": title,
                        "snippet": cleaned_content,
                        "url": url,
                        "is_answer": False
                    })
                
                return results
            elif self.provider == "serpapi":
                # SerpAPI search
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
                # DuckDuckGo search
                results = []
                if hasattr(engine, 'text'):
                    for result in engine.text(query, max_results=max_results):
                        if result:  # Check if result is not None
                            results.append({
                                "title": result.get("title", ""),
                                "snippet": result.get("body", ""),
                                "url": result.get("href", "")
                            })
                else:
                    logger.error("DuckDuckGo engine does not have 'text' method")
                return results
                
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}", exc_info=True)
            return []
    
    def _clean_content(self, content: str, max_length: int = 500) -> str:
        """Clean and truncate content.
        
        Args:
            content: Raw content string
            max_length: Maximum length for snippet
            
        Returns:
            Cleaned and truncated content
        """
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = " ".join(content.split())
        
        # Remove common noise patterns
        content = content.replace("\n\n\n", "\n\n")
        content = content.replace("  ", " ")
        
        # Truncate intelligently (at sentence boundary if possible)
        if len(content) > max_length:
            truncated = content[:max_length]
            # Try to cut at sentence boundary
            last_period = truncated.rfind(". ")
            last_exclamation = truncated.rfind("! ")
            last_question = truncated.rfind("? ")
            last_break = max(last_period, last_exclamation, last_question)
            
            if last_break > max_length * 0.7:  # Only use if not too short
                content = truncated[:last_break + 1] + "..."
            else:
                content = truncated + "..."
        
        return content.strip()
    
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
        
        formatted = ""
        
        # Separate answer/summary from individual results
        answer_results = [r for r in results if r.get("is_answer", False)]
        regular_results = [r for r in results if not r.get("is_answer", False)]
        
        # Add answer/summary first if available
        if answer_results:
            answer = answer_results[0]
            formatted += f"**Summary:**\n{answer['snippet']}\n\n"
        
        # Add individual results
        if regular_results:
            formatted += "**Sources:**\n\n"
            for i, result in enumerate(regular_results, 1):
                title = result.get('title', 'Untitled')
                snippet = result.get('snippet', '')
                url = result.get('url', '')
                
                formatted += f"{i}. **{title}**\n"
                if snippet:
                    formatted += f"   {snippet}\n"
                if url:
                    formatted += f"   🔗 {url}\n"
                formatted += "\n"
        
        return formatted.strip()
