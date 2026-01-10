"""Grounded Q&A agent for chat flow."""

import logging
from typing import List, Tuple, Optional, Dict
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.config.settings import config

logger = logging.getLogger(__name__)


class QAAgent:
    """Generates grounded answers with citations."""
    
    def __init__(self):
        """Initialize Q&A agent."""
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
    
    def answer(
        self,
        query: str,
        context_chunks: List[Tuple[Document, float]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        tool_context: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Generate grounded answer with citations.
        
        Args:
            query: User query
            context_chunks: List of (Document, score) tuples from retrieval
            chat_history: Optional conversation history
            
        Returns:
            Tuple of (answer_text, citations_list)
        """
        if not context_chunks:
            return "Not available in the document.", []
        
        try:
            # Format context from chunks
            context_text = self._format_context(context_chunks)
            
            # Format chat history
            history_text = self._format_history(chat_history) if chat_history else ""
            
            # Format tool context if available
            tool_text = f"\n\n**Additional Context from Tools:**\n{tool_context}" if tool_context else ""
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful assistant that answers questions about BFSI (Banking, Financial Services, and Insurance) documents.

**CRITICAL RULES:**
1. Answer STRICTLY based on the provided document context
2. If the information is not in the context, respond with: "Not available in the document."
3. Cite specific chunks when referencing information (use [Chunk X] format)
4. Be accurate and precise with financial numbers
5. Do not make up or infer information not present in the context
6. If asked about something not in the document, clearly state it's not available
7. You may combine document information with tool-provided context when relevant

**Context from Document:**
{context}

**Previous Conversation:**
{history}
{tool_context}

Answer the user's question based on the context provided. Include citations in [Chunk X] format."""),
                ("human", "Question: {query}\n\nAnswer:")
            ])
            
            # Generate answer
            formatted_prompt = prompt.format_messages(
                context=context_text,
                history=history_text,
                tool_context=tool_text,
                query=query
            )
            
            response = self.llm.invoke(formatted_prompt)
            
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)
            
            # Extract citations
            citations = self._extract_citations(answer, context_chunks)
            
            logger.info(f"Generated answer with {len(citations)} citations")
            return answer, citations
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            # Return a helpful error message instead of "not available"
            error_msg = f"I encountered an error while processing your query: {str(e)}. Please try again or rephrase your question."
            return error_msg, []
    
    def _format_context(self, chunks: List[Tuple[Document, float]]) -> str:
        """Format context chunks for prompt."""
        context_parts = []
        for i, (doc, score) in enumerate(chunks, 1):
            page = doc.metadata.get('page', 'N/A')
            section = doc.metadata.get('section', 'N/A')
            content = doc.page_content[:500]  # Limit chunk preview
            context_parts.append(
                f"[Chunk {i}] (Page {page}, Section: {section}, Relevance: {score:.3f})\n"
                f"{content}\n"
            )
        return "\n".join(context_parts)
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format chat history for prompt."""
        if not history:
            return "No previous conversation."
        
        history_parts = []
        for msg in history[-5:]:  # Last 5 exchanges
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            history_parts.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(history_parts)
    
    def _extract_citations(
        self,
        answer: str,
        chunks: List[Tuple[Document, float]]
    ) -> List[Dict[str, str]]:
        """Extract citation references from answer.
        
        Returns:
            List of citation dictionaries with chunk info
        """
        citations = []
        
        # Find chunk references in answer (e.g., [Chunk 1], [Chunk 2])
        import re
        chunk_refs = re.findall(r'\[Chunk\s+(\d+)\]', answer, re.IGNORECASE)
        
        for ref in set(chunk_refs):  # Unique references
            try:
                chunk_idx = int(ref) - 1  # Convert to 0-based index
                if 0 <= chunk_idx < len(chunks):
                    doc, score = chunks[chunk_idx]
                    citations.append({
                        "chunk_id": ref,
                        "page": doc.metadata.get('page', 'N/A'),
                        "section": doc.metadata.get('section', 'N/A'),
                        "preview": doc.page_content[:200],
                        "relevance_score": f"{score:.3f}"
                    })
            except (ValueError, IndexError):
                continue
        
        return citations
