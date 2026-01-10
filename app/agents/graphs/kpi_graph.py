"""LangGraph workflow for KPI report generation."""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document

from app.agents.graphs.state import KPIState
from app.agents.kpi.retrieval_agent import RetrievalAgent
from app.agents.kpi.financial_analysis_agent import FinancialAnalysisAgent
from app.agents.kpi.report_generation_agent import ReportGenerationAgent
from app.ingestion.vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)


class KPIGraph:
    """LangGraph workflow for KPI report generation."""
    
    def __init__(self, vector_store: FAISSVectorStore):
        """Initialize KPI graph.
        
        Args:
            vector_store: FAISSVectorStore instance
        """
        self.vector_store = vector_store
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the KPI generation graph.
        
        Flow: START -> retrieval -> financial_analysis -> report_generation -> END
        """
        workflow = StateGraph(KPIState)
        
        # Add nodes
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("financial_analysis", self._financial_analysis_node)
        workflow.add_node("report_generation", self._report_generation_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Define edges
        workflow.set_entry_point("retrieval")
        workflow.add_edge("retrieval", "financial_analysis")
        workflow.add_edge("financial_analysis", "report_generation")
        workflow.add_edge("report_generation", END)
        
        # Error handling
        workflow.add_conditional_edges(
            "retrieval",
            self._check_error,
            {
                "error": "error_handler",
                "continue": "financial_analysis"
            }
        )
        workflow.add_conditional_edges(
            "financial_analysis",
            self._check_error,
            {
                "error": "error_handler",
                "continue": "report_generation"
            }
        )
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    def _retrieval_node(self, state: KPIState) -> KPIState:
        """Retrieval node: Get relevant chunks for KPI extraction."""
        try:
            logger.info("Executing retrieval node")
            retrieval_agent = RetrievalAgent(self.vector_store)
            chunks = retrieval_agent.retrieve(state.get("query"))
            
            if not chunks:
                state["error"] = "No relevant chunks retrieved for KPI extraction"
                return state
            
            state["chunks"] = chunks
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            return state
            
        except Exception as e:
            logger.error(f"Error in retrieval node: {str(e)}")
            state["error"] = f"Retrieval error: {str(e)}"
            return state
    
    def _financial_analysis_node(self, state: KPIState) -> KPIState:
        """Financial analysis node: Extract KPIs from chunks."""
        try:
            logger.info("Executing financial analysis node")
            financial_agent = FinancialAnalysisAgent()
            kpi_data = financial_agent.extract_kpis(state["chunks"])
            
            state["kpi_data"] = kpi_data
            logger.info("Extracted KPI data")
            return state
            
        except Exception as e:
            logger.error(f"Error in financial analysis node: {str(e)}")
            state["error"] = f"Financial analysis error: {str(e)}"
            return state
    
    def _report_generation_node(self, state: KPIState) -> KPIState:
        """Report generation node: Generate structured report."""
        try:
            logger.info("Executing report generation node")
            report_agent = ReportGenerationAgent()
            report = report_agent.generate_report(state["kpi_data"])
            
            state["report"] = report
            state["chunks_used"] = len(state["chunks"])
            logger.info("Generated KPI report")
            return state
            
        except Exception as e:
            logger.error(f"Error in report generation node: {str(e)}")
            state["error"] = f"Report generation error: {str(e)}"
            return state
    
    def _error_handler_node(self, state: KPIState) -> KPIState:
        """Error handler node."""
        error = state.get("error", "Unknown error")
        logger.error(f"KPI flow error: {error}")
        state["report"] = f"Error generating KPI report: {error}"
        return state
    
    def _check_error(self, state: KPIState) -> str:
        """Check if there's an error in the state."""
        return "error" if state.get("error") else "continue"
    
    def run(self, query: str = None) -> Dict[str, Any]:
        """Execute the KPI generation workflow.
        
        Args:
            query: Optional specific query (defaults to KPI-focused query)
            
        Returns:
            Dictionary with report, kpi_data, and chunks_used
        """
        if query is None:
            query = (
                "financial metrics revenue profit ROE ROA GNPA NNPA PCR CRAR CAR "
                "quarterly results annual report growth percentage"
            )
        
        initial_state: KPIState = {
            "query": query,
            "chunks": [],
            "kpi_data": {},
            "report": "",
            "chunks_used": 0,
            "error": None
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            if final_state.get("error"):
                raise ValueError(final_state["error"])
            
            return {
                "report": final_state["report"],
                "kpi_data": final_state["kpi_data"],
                "chunks_used": final_state["chunks_used"]
            }
            
        except Exception as e:
            logger.error(f"Error in KPI graph execution: {str(e)}")
            raise

