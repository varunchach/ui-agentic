"""State schemas for LangGraph workflows."""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from langchain_core.documents import Document


class KPIState(TypedDict):
    """State for KPI report generation flow."""
    query: str
    chunks: List[Document]
    kpi_data: Dict[str, Any]
    report: str
    chunks_used: int
    error: Optional[str]


class ChatState(TypedDict):
    """State for chat flow with agentic RAG."""
    query: str
    refined_query: str
    routing_decision: Dict[str, Any]
    route: Literal["rag", "tool", "both"]
    tool_name: Optional[str]
    tool_params: Optional[Dict[str, Any]]
    tool_output: Optional[str]
    chunks: List[Document]
    chunk_scores: Dict[int, float]  # Store scores for chunks
    answer: str
    citations: List[Dict[str, str]]
    chat_history: List[Dict[str, str]]
    tool_used: Optional[str]
    error: Optional[str]

