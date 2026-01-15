"""Tool registry for agentic RAG system."""

import logging
from typing import Dict, Callable, Any, Optional
from app.tools.web_search import WebSearchTool
from app.tools.finance_tool import FinanceTool
from app.tools.gdp_tool import GDPTool
from app.config.settings import config

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available tools for the agentic system."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Callable] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools."""
        import os
        
        # Web Search Tool (Tavily recommended for RAG)
        web_search_key = os.getenv("TAVILY_API_KEY") or os.getenv("SERPAPI_API_KEY") or os.getenv("WEB_SEARCH_API_KEY")
        web_search_provider = os.getenv("WEB_SEARCH_PROVIDER", "tavily")
        self.tools["web_search"] = WebSearchTool(
            api_key=web_search_key,
            provider=web_search_provider
        )
        logger.info(f"Registered web_search tool with provider: {web_search_provider}")
        
        # Finance Tool
        self.tools["finance"] = FinanceTool()
        logger.info("Registered finance tool")
        
        # GDP Tool
        gdp_api_key = os.getenv("FRED_API_KEY") or os.getenv("GDP_API_KEY")
        self.tools["gdp"] = GDPTool(api_key=gdp_api_key)
        logger.info("Registered gdp tool")
    
    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool callable or None if not found
        """
        return self.tools.get(tool_name)
    
    def list_tools(self) -> Dict[str, str]:
        """List all available tools with descriptions.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            "web_search": "Search the web for real-time information, news, and current events",
            "finance": "Get stock prices, market data, and financial information using yfinance",
            "gdp": "Get GDP data and economic indicators for countries",
        }
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool output as string
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
        
        try:
            if tool_name == "web_search":
                query = kwargs.get("query", "")
                if not query or not query.strip():
                    logger.warning(f"Empty query provided to web_search tool. kwargs: {kwargs}")
                    return "Error: No search query provided. Please provide a valid search query."
                return tool(query)
            elif tool_name == "finance":
                action = kwargs.get("action", "stock_info")
                symbol = kwargs.get("symbol")
                # Remove action and symbol from kwargs to avoid duplicate arguments
                kwargs_clean = {k: v for k, v in kwargs.items() if k not in ["action", "symbol"]}
                return tool(action, symbol, **kwargs_clean)
            elif tool_name == "gdp":
                action = kwargs.get("action", "gdp")
                country = kwargs.get("country", "US")
                # Remove action and country from kwargs to avoid duplicate arguments
                kwargs_clean = {k: v for k, v in kwargs.items() if k not in ["country", "action"]}
                return tool(action, country=country, **kwargs_clean)
            else:
                return f"Tool '{tool_name}' execution not implemented"
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return f"Error executing tool: {str(e)}"


# Global tool registry instance
tool_registry = ToolRegistry()
