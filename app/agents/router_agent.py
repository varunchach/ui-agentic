"""Router agent that decides between RAG and tools."""

import logging
from typing import Literal, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate

from app.config.settings import config
from app.tools.tool_registry import tool_registry

logger = logging.getLogger(__name__)


class RouterAgent:
    """Agent that routes queries to RAG or tools."""
    
    def __init__(self):
        """Initialize router agent."""
        self.llm = self._get_llm()
        self.tool_registry = tool_registry
    
    def _get_llm(self):
        """Get LLM instance."""
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
                raise ImportError("langchain-anthropic not installed")
        elif provider == "custom":
            from langchain_openai import ChatOpenAI
            from app.utils.llm_optimizations import apply_llm_optimizations
            
            llm = ChatOpenAI(
                model=config.llm.model,
                temperature=config.llm.temperature,
                base_url=config.llm.endpoint,
                api_key=config.llm.api_key or "dummy"
            )
            return apply_llm_optimizations(llm)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def route(
        self,
        query: str,
        has_document_context: bool = True
    ) -> Dict[str, Any]:
        """Route query to RAG or tools.
        
        Args:
            query: User query
            has_document_context: Whether document context is available
            
        Returns:
            Dictionary with routing decision and tool info if needed
        """
        try:
            # Get available tools
            available_tools = self.tool_registry.list_tools()
            tools_description = "\n".join([
                f"- {name}: {desc}" for name, desc in available_tools.items()
            ])
            
            # Create routing prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a routing agent that decides whether to use RAG (document retrieval) or external tools.

**Available Tools:**
{tools}

**Routing Rules:**
1. Use RAG if:
   - Query is about the uploaded document
   - Query asks about specific content in the document
   - Query references information that should be in the document
   - Query is about BFSI KPIs, financial metrics from the document

2. Use Tools if:
   - Query asks for real-time information (current stock prices, news)
   - Query asks for data not in the document (GDP, economic indicators)
   - Query asks for general market information
   - Query asks "what is" or "tell me about" for general topics
   - Query needs web search for current events

3. Use Both if:
   - Query needs document context AND real-time data
   - Query compares document data with current market data

**Response Format (JSON):**
{{
    "route": "rag" | "tool" | "both",
    "tool_name": "tool_name" or null,
    "tool_params": {{}} or null,
    "reasoning": "brief explanation"
}}"""),
                ("human", """Query: {query}
Has Document Context: {has_context}

Route this query:""")
            ])
            
            formatted_prompt = prompt.format_messages(
                tools=tools_description,
                query=query,
                has_context=has_document_context
            )
            
            response = self.llm.invoke(formatted_prompt)
            
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                routing_decision = json.loads(json_match.group())
            else:
                # Fallback: simple heuristic
                routing_decision = self._heuristic_route(query, has_document_context)
            
            logger.info(f"Routing decision: {routing_decision.get('route')} for query: {query[:50]}")
            return routing_decision
            
        except Exception as e:
            logger.error(f"Error in routing: {str(e)}")
            # Fallback to heuristic
            return self._heuristic_route(query, has_document_context)
    
    def _heuristic_route(self, query: str, has_context: bool) -> Dict[str, Any]:
        """Heuristic routing fallback.
        
        Args:
            query: User query
            has_context: Whether document context is available
            
        Returns:
            Routing decision
        """
        query_lower = query.lower()
        
        # Keywords that suggest tool usage
        tool_keywords = [
            "current", "today", "latest", "now", "real-time",
            "stock", "price", "market", "gdp", "economic",
            "search", "find", "what is", "tell me about"
        ]
        
        # Keywords that suggest RAG
        rag_keywords = [
            "document", "report", "in the document", "from the document",
            "kpi", "revenue", "profit", "npa", "crar", "car"
        ]
        
        tool_score = sum(1 for keyword in tool_keywords if keyword in query_lower)
        rag_score = sum(1 for keyword in rag_keywords if keyword in query_lower)
        
        if tool_score > rag_score and tool_score > 0:
            # Determine which tool
            if any(kw in query_lower for kw in ["stock", "price", "market", "finance"]):
                return {
                    "route": "tool",
                    "tool_name": "finance",
                    "tool_params": {"action": "stock_info", "symbol": self._extract_symbol(query)},
                    "reasoning": "Query about stock/market data"
                }
            elif any(kw in query_lower for kw in ["gdp", "economic", "country"]):
                return {
                    "route": "tool",
                    "tool_name": "gdp",
                    "tool_params": {"action": "gdp", "country": self._extract_country(query)},
                    "reasoning": "Query about GDP/economic data"
                }
            else:
                return {
                    "route": "tool",
                    "tool_name": "web_search",
                    "tool_params": {"query": query},
                    "reasoning": "Query needs web search"
                }
        elif has_context and (rag_score > 0 or tool_score == 0):
            return {
                "route": "rag",
                "tool_name": None,
                "tool_params": None,
                "reasoning": "Query about document content"
            }
        else:
            return {
                "route": "tool",
                "tool_name": "web_search",
                "tool_params": {"query": query},
                "reasoning": "General query, no document context"
            }
    
    def _extract_symbol(self, query: str) -> Optional[str]:
        """Extract stock symbol from query."""
        import re
        # Look for common patterns like "AAPL", "MSFT", etc.
        symbol_match = re.search(r'\b[A-Z]{2,5}\b', query.upper())
        return symbol_match.group() if symbol_match else None
    
    def _extract_country(self, query: str) -> str:
        """Extract country code from query."""
        query_lower = query.lower()
        country_map = {
            "usa": "US", "united states": "US", "america": "US",
            "india": "IN", "indian": "IN",
            "china": "CN", "chinese": "CN",
            "uk": "GB", "united kingdom": "GB", "britain": "GB",
        }
        for key, code in country_map.items():
            if key in query_lower:
                return code
        return "US"  # Default
