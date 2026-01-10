"""LangGraph workflow for agentic chat with RAG and tools."""

import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from app.agents.graphs.state import ChatState
from app.agents.router_agent import RouterAgent
from app.agents.chat.query_understanding_agent import QueryUnderstandingAgent
from app.agents.chat.retrieval_rerank_agent import RetrievalRerankAgent
from app.agents.chat.qa_agent import QAAgent
from app.tools.tool_registry import tool_registry
from app.ingestion.vector_store import FAISSVectorStore

logger = logging.getLogger(__name__)


class ChatGraph:
    """LangGraph workflow for agentic chat with RAG and tools."""
    
    def __init__(self, vector_store: FAISSVectorStore):
        """Initialize chat graph.
        
        Args:
            vector_store: FAISSVectorStore instance
        """
        self.vector_store = vector_store
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the chat graph.
        
        Flow: START -> router -> [rag_path | tool_path | both_path] -> combine -> END
        """
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("query_understanding", self._query_understanding_node)
        workflow.add_node("retrieval_rerank", self._retrieval_rerank_node)
        workflow.add_node("qa", self._qa_node)
        workflow.add_node("tool_execution", self._tool_execution_node)
        workflow.add_node("combine_results", self._combine_results_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Define entry point
        workflow.set_entry_point("router")
        
        # Conditional routing after router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "rag": "query_understanding",
                "tool": "tool_execution",
                "both": "query_understanding",  # Start with RAG, then tool
                "error": "error_handler"
            }
        )
        
        # RAG path: query understanding -> retrieval -> QA
        workflow.add_edge("query_understanding", "retrieval_rerank")
        workflow.add_edge("retrieval_rerank", "qa")
        
        # After QA, check if we need tool execution (for "both" route)
        workflow.add_conditional_edges(
            "qa",
            self._check_if_both_after_qa,
            {
                "both": "tool_execution",
                "done": "combine_results"
            }
        )
        
        # Tool path: tool execution -> combine
        workflow.add_edge("tool_execution", "combine_results")
        
        # Combine and end
        workflow.add_edge("combine_results", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    def _router_node(self, state: ChatState) -> ChatState:
        """Router node: Decide between RAG, tools, or both."""
        try:
            logger.info(f"Executing router node for query: {state['query'][:50]}...")
            router = RouterAgent()
            routing_decision = router.route(
                query=state["query"],
                has_document_context=self.vector_store is not None
            )
            
            state["routing_decision"] = routing_decision
            state["route"] = routing_decision.get("route", "rag")
            state["tool_name"] = routing_decision.get("tool_name")
            state["tool_params"] = routing_decision.get("tool_params", {})
            
            logger.info(f"Router decision: {state['route']}, tool: {state['tool_name']}")
            return state
            
        except Exception as e:
            logger.error(f"Error in router node: {str(e)}")
            state["error"] = f"Router error: {str(e)}"
            state["route"] = "error"
            return state
    
    def _query_understanding_node(self, state: ChatState) -> ChatState:
        """Query understanding node: Refine query for better retrieval."""
        try:
            logger.info("Executing query understanding node")
            query_agent = QueryUnderstandingAgent()
            refined_query = query_agent.understand_query(state["query"])
            
            state["refined_query"] = refined_query
            logger.debug(f"Refined query: {refined_query}")
            return state
            
        except Exception as e:
            logger.warning(f"Error in query understanding, using original: {str(e)}")
            state["refined_query"] = state["query"]
            return state
    
    def _retrieval_rerank_node(self, state: ChatState) -> ChatState:
        """Retrieval and re-ranking node: Get relevant chunks."""
        try:
            logger.info("Executing retrieval and re-ranking node")
            
            # Check if we have document context
            if self.vector_store is None:
                if state.get("route") == "rag":
                    state["error"] = "No document uploaded. Please upload a document first."
                    state["chunks"] = []
                    return state
                else:
                    # For "both" or "tool" routes, continue without chunks
                    state["chunks"] = []
                    return state
            
            retrieval_agent = RetrievalRerankAgent(self.vector_store)
            chunks_with_scores = retrieval_agent.retrieve_and_rerank(state["refined_query"])
            
            # Store both chunks and scores for later use
            chunks = [doc for doc, score in chunks_with_scores]
            state["chunks"] = chunks
            state["chunk_scores"] = {i: score for i, (doc, score) in enumerate(chunks_with_scores)}
            
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            return state
            
        except Exception as e:
            logger.error(f"Error in retrieval and re-ranking: {str(e)}")
            state["chunks"] = []
            return state
    
    def _qa_node(self, state: ChatState) -> ChatState:
        """Q&A node: Generate grounded answer with citations."""
        try:
            logger.info("Executing Q&A node")
            
            if not state.get("chunks"):
                state["answer"] = "Not available in the document."
                state["citations"] = []
                return state
            
            qa_agent = QAAgent()
            
            # Convert chunks to (Document, score) format for QAAgent
            chunks_with_scores = []
            chunk_scores = state.get("chunk_scores", {})
            for i, chunk in enumerate(state["chunks"]):
                # Use actual score if available, otherwise use placeholder
                score = chunk_scores.get(i, 1.0 - (i * 0.1))
                chunks_with_scores.append((chunk, score))
            
            answer, citations = qa_agent.answer(
                query=state["query"],
                context_chunks=chunks_with_scores,
                chat_history=state.get("chat_history"),
                tool_context=state.get("tool_output") if state["route"] == "both" else None
            )
            
            state["answer"] = answer
            state["citations"] = citations
            return state
            
        except Exception as e:
            logger.error(f"Error in Q&A node: {str(e)}", exc_info=True)
            # If we have chunks but LLM failed, provide helpful error
            if state.get("chunks"):
                state["answer"] = f"I encountered an error while processing your query: {str(e)}. The document content was retrieved, but I couldn't generate a response. Please try again."
            else:
                state["answer"] = "Not available in the document."
            state["citations"] = []
            return state
    
    def _tool_execution_node(self, state: ChatState) -> ChatState:
        """Tool execution node: Execute external tool."""
        try:
            logger.info(f"Executing tool: {state.get('tool_name')}")
            
            if not state.get("tool_name"):
                state["tool_output"] = "No tool specified"
                return state
            
            tool_output = tool_registry.execute_tool(
                state["tool_name"],
                **state.get("tool_params", {})
            )
            
            state["tool_output"] = tool_output
            state["tool_used"] = state["tool_name"]
            logger.info(f"Tool {state['tool_name']} executed")
            return state
            
        except Exception as e:
            logger.error(f"Error in tool execution: {str(e)}")
            state["tool_output"] = f"Error executing tool: {str(e)}"
            return state
    
    def _combine_results_node(self, state: ChatState) -> ChatState:
        """Combine results node: Merge RAG and tool outputs."""
        try:
            logger.info("Executing combine results node")
            
            answer = state.get("answer", "")
            tool_output = state.get("tool_output")
            route = state.get("route", "rag")
            
            # If only tool was used, format tool output as answer
            if route == "tool" and tool_output:
                answer = tool_output
                state["answer"] = answer
            
            # If both were used, combine answers
            elif route == "both" and tool_output and answer:
                answer = f"{answer}\n\n**Additional Information from Tools:**\n{tool_output}"
                state["answer"] = answer
            
            # If only RAG was used, answer is already set
            
            # Update chat history
            chat_history = state.get("chat_history", [])
            updated_history = chat_history + [
                {"role": "user", "content": state["query"]},
                {"role": "assistant", "content": answer}
            ]
            state["chat_history"] = updated_history
            
            logger.info(f"Combined results for route: {route}")
            return state
            
        except Exception as e:
            logger.error(f"Error in combine results: {str(e)}")
            state["error"] = f"Combine results error: {str(e)}"
            return state
    
    def _error_handler_node(self, state: ChatState) -> ChatState:
        """Error handler node."""
        error = state.get("error", "Unknown error")
        logger.error(f"Chat flow error: {error}")
        state["answer"] = f"Error: {error}"
        state["citations"] = []
        return state
    
    def _route_decision(self, state: ChatState) -> str:
        """Determine next step based on routing decision."""
        if state.get("error"):
            return "error"
        return state.get("route", "rag")
    
    def _check_if_both_after_qa(self, state: ChatState) -> str:
        """Check if we need to execute tool after QA (for 'both' route)."""
        if state.get("route") == "both" and not state.get("tool_output"):
            return "both"
        return "done"
    
    def run(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute the chat workflow.
        
        Args:
            query: User query
            chat_history: Optional conversation history
            
        Returns:
            Dictionary with answer, citations, tool_used, and updated history
        """
        initial_state: ChatState = {
            "query": query,
            "refined_query": "",
            "routing_decision": {},
            "route": "rag",
            "tool_name": None,
            "tool_params": None,
            "tool_output": None,
            "chunks": [],
            "chunk_scores": {},
            "answer": "",
            "citations": [],
            "chat_history": chat_history or [],
            "tool_used": None,
            "error": None
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            if final_state.get("error"):
                logger.warning(f"Chat flow completed with error: {final_state['error']}")
            
            return {
                "answer": final_state["answer"],
                "citations": final_state["citations"],
                "tool_used": final_state.get("tool_used"),
                "chat_history": final_state["chat_history"]
            }
            
        except Exception as e:
            logger.error(f"Error in chat graph execution: {str(e)}")
            raise

