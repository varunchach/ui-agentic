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
   - Query mentions "in the document", "from the document", "document says"

2. Use Tools if:
   - Query asks for real-time information (current stock prices, news)
   - Query asks for data not in the document (GDP, economic indicators, country data)
   - Query asks for general market information
   - Query asks "what is" or "tell me about" for general topics (GDP, stock prices, etc.)
   - Query needs web search for current events
   - Query mentions "GDP", "economic", "country", "stock price", "current price"

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
            
            logger.debug(f"LLM routing response: {content[:300]}")
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response (handle nested braces)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                try:
                    routing_decision = json.loads(json_match.group())
                    # Validate routing decision
                    if not routing_decision.get('route') or routing_decision.get('route') not in ['rag', 'tool', 'both']:
                        logger.warning(f"Invalid route in LLM response: {routing_decision}, using heuristic")
                        routing_decision = self._heuristic_route(query, has_document_context)
                    else:
                        # Ensure tool_params exists
                        if routing_decision.get('tool_name') and 'tool_params' not in routing_decision:
                            routing_decision['tool_params'] = {}
                        
                        # Normalize country names to codes for GDP tool
                        if routing_decision.get('tool_name') == 'gdp' and routing_decision.get('tool_params'):
                            country = routing_decision['tool_params'].get('country')
                            if country:
                                normalized_country = self._normalize_country_name(country)
                                routing_decision['tool_params']['country'] = normalized_country
                            # Extract year if not already present
                            if 'year' not in routing_decision.get('tool_params', {}):
                                year = self._extract_year(query)
                                if year:
                                    routing_decision['tool_params']['year'] = year
                        
                        # Ensure web_search always has query in tool_params
                        if routing_decision.get('tool_name') == 'web_search':
                            if not routing_decision.get('tool_params'):
                                routing_decision['tool_params'] = {}
                            if 'query' not in routing_decision['tool_params'] or not routing_decision['tool_params'].get('query'):
                                routing_decision['tool_params']['query'] = query
                        
                        logger.info(f"LLM routing successful: {routing_decision.get('route')} -> {routing_decision.get('tool_name')}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from LLM response: {e}, content: {content[:200]}, using heuristic")
                    routing_decision = self._heuristic_route(query, has_document_context)
            else:
                # Fallback: simple heuristic
                logger.warning(f"No JSON found in LLM response: {content[:200]}, using heuristic")
                routing_decision = self._heuristic_route(query, has_document_context)
            
            logger.info(f"Final routing decision: {routing_decision.get('route')} for query: {query[:50]}")
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
        
        # Strong tool indicators (check first - these override everything)
        strong_tool_indicators = ["gdp", "economic indicator", "stock price", "current price", "market data"]
        if any(indicator in query_lower for indicator in strong_tool_indicators):
            # Determine which tool
            if any(kw in query_lower for kw in ["gdp", "economic", "country", "economy"]):
                year = self._extract_year(query)
                return {
                    "route": "tool",
                    "tool_name": "gdp",
                    "tool_params": {"action": "gdp", "country": self._extract_country(query), "year": year},
                    "reasoning": "Query about GDP/economic data"
                }
            elif any(kw in query_lower for kw in ["stock", "price", "market", "finance"]):
                return {
                    "route": "tool",
                    "tool_name": "finance",
                    "tool_params": {"action": "stock_info", "symbol": self._extract_symbol(query)},
                    "reasoning": "Query about stock/market data"
                }
        
        # Keywords that suggest tool usage
        tool_keywords = [
            "current", "today", "latest", "now", "real-time",
            "stock", "price", "market", "gdp", "economic", "economy",
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
            # But check if it's clearly a tool query first
            if any(kw in query_lower for kw in ["gdp", "economic", "economy", "country"]):
                return {
                    "route": "tool",
                    "tool_name": "gdp",
                    "tool_params": {"action": "gdp", "country": self._extract_country(query)},
                    "reasoning": "Query about GDP/economic data (overrides document context)"
                }
            return {
                "route": "rag",
                "tool_name": None,
                "tool_params": None,
                "reasoning": "Query about document content"
            }
        else:
            # No document context - check for tool queries
            if any(kw in query_lower for kw in ["gdp", "economic", "economy", "country"]):
                return {
                    "route": "tool",
                    "tool_name": "gdp",
                    "tool_params": {"action": "gdp", "country": self._extract_country(query)},
                    "reasoning": "Query about GDP/economic data"
                }
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
            "usa": "US", "united states": "US", "america": "US", "us": "US",
            "india": "IN", "indian": "IN", "in": "IN",
            "china": "CN", "chinese": "CN", "cn": "CN",
            "uk": "GB", "united kingdom": "GB", "britain": "GB", "gb": "GB",
        }
        for key, code in country_map.items():
            if key in query_lower:
                return code
        return "US"  # Default
    
    def _extract_year(self, query: str) -> Optional[int]:
        """Extract year from query.
        
        Args:
            query: User query
            
        Returns:
            Year as integer or None if not found
        """
        import re
        # Look for 4-digit years (1900-2099)
        year_match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', query)
        if year_match:
            try:
                return int(year_match.group(1))
            except (ValueError, AttributeError):
                pass
        return None
    
    def _normalize_country_name(self, country: str) -> str:
        """Normalize country name to country code.
        
        Args:
            country: Country name or code
            
        Returns:
            Country code (US, IN, CN, etc.)
        """
        country_lower = country.lower().strip()
        country_map = {
            "usa": "US", "united states": "US", "america": "US", "us": "US",
            "india": "IN", "indian": "IN", "in": "IN",
            "china": "CN", "chinese": "CN", "cn": "CN",
            "uk": "GB", "united kingdom": "GB", "britain": "GB", "gb": "GB",
            "germany": "DE", "de": "DE",
            "france": "FR", "fr": "FR",
            "japan": "JP", "jp": "JP",
        }
        for key, code in country_map.items():
            if key in country_lower:
                return code
        # If not found, try to use as-is if it's already a 2-letter code
        if len(country) == 2 and country.isupper():
            return country
        # Default to US
        return "US"
