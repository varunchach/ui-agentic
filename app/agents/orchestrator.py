"""Agent orchestrator/router for KPI and Chat flows using LangGraph."""

import logging
import time
from typing import Literal, Optional, Any

from app.ingestion.vector_store import FAISSVectorStore
from app.agents.graphs.kpi_graph import KPIGraph
from app.agents.graphs.chat_graph import ChatGraph

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates agent execution for different flows using LangGraph."""
    
    def __init__(self, vector_store: Optional[FAISSVectorStore] = None):
        """Initialize orchestrator.
        
        Args:
            vector_store: Optional FAISSVectorStore instance
        """
        self.vector_store = vector_store
        self._kpi_graph = None
        self._chat_graph = None
    
    def set_vector_store(self, vector_store: FAISSVectorStore):
        """Set or update the vector store and rebuild graphs."""
        self.vector_store = vector_store
        self._kpi_graph = None
        self._chat_graph = None
        logger.info("Vector store updated in orchestrator, graphs will be rebuilt on next use")
    
    def _get_kpi_graph(self) -> KPIGraph:
        """Get or create KPI graph."""
        if self.vector_store is None:
            raise ValueError("Vector store not set. Cannot execute agents.")
        
        if self._kpi_graph is None:
            self._kpi_graph = KPIGraph(self.vector_store)
            logger.info("KPI graph initialized")
        
        return self._kpi_graph
    
    def _get_chat_graph(self) -> ChatGraph:
        """Get or create chat graph."""
        if self.vector_store is None:
            raise ValueError("Vector store not set. Cannot execute agents.")
        
        if self._chat_graph is None:
            self._chat_graph = ChatGraph(self.vector_store)
            logger.info("Chat graph initialized")
        
        return self._chat_graph
    
    def execute(
        self,
        flow_type: Literal["kpi_report", "chat"],
        **kwargs
    ) -> Any:
        """Execute agent flow based on type using LangGraph.
        
        Args:
            flow_type: Type of flow to execute ("kpi_report" or "chat")
            **kwargs: Flow-specific arguments
            
        Returns:
            Flow-specific result
        """
        if self.vector_store is None:
            raise ValueError("Vector store not set. Cannot execute agents.")
        
        if flow_type == "kpi_report":
            return self._execute_kpi_flow(**kwargs)
        elif flow_type == "chat":
            return self._execute_chat_flow(**kwargs)
        else:
            raise ValueError(f"Unknown flow type: {flow_type}")
    
    def _execute_kpi_flow(self, **kwargs) -> dict:
        """Execute KPI report generation flow using LangGraph.
        
        Returns:
            Dictionary with report content and metadata, including execution_time
        """
        logger.info("Starting KPI report flow (LangGraph)")
        start_time = time.time()
        
        try:
            kpi_graph = self._get_kpi_graph()
            query = kwargs.get("query", None)
            result = kpi_graph.run(query=query)
            
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            logger.info(f"KPI report flow completed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in KPI flow after {execution_time:.2f}s: {str(e)}")
            raise
    
    def _execute_chat_flow(self, query: str, chat_history: Optional[list] = None, **kwargs) -> dict:
        """Execute agentic chat flow with RAG and tools using LangGraph.
        
        Args:
            query: User query
            chat_history: Optional conversation history
            
        Returns:
            Dictionary with answer, citations, tool_used, updated history, and execution_time
        """
        logger.info(f"Starting agentic chat flow (LangGraph) for query: {query[:50]}...")
        start_time = time.time()
        
        try:
            chat_graph = self._get_chat_graph()
            result = chat_graph.run(query=query, chat_history=chat_history)
            
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            logger.info(f"Chat flow completed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in chat flow after {execution_time:.2f}s: {str(e)}")
            raise
