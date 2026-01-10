"""Chat view component for document Q&A."""

import streamlit as st
from typing import List, Dict


def render_chat_interface():
    """Render chat interface for document Q&A."""
    st.header("💬 Chat with Document")
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat history
    st.markdown("---")
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            citations = message.get('citations', [])
            
            if role == 'user':
                with st.chat_message("user"):
                    st.write(content)
            else:
                with st.chat_message("assistant"):
                    st.write(content)
                    
                    # Display execution time
                    execution_time = message.get('execution_time')
                    if execution_time is not None:
                        time_str = f"{execution_time:.2f}s" if execution_time < 60 else f"{execution_time/60:.1f}m"
                        st.caption(f"⏱️ Response time: {time_str}")
                    
                    # Display tool used if available
                    tool_used = message.get('tool_used')
                    if tool_used:
                        st.caption(f"🔧 Used tool: {tool_used}")
                    
                    # Display citations if available
                    if citations:
                        with st.expander(f"📚 Citations ({len(citations)})"):
                            for citation in citations:
                                st.markdown(f"**Chunk {citation.get('chunk_id', 'N/A')}**")
                                st.caption(f"Page: {citation.get('page', 'N/A')} | "
                                          f"Section: {citation.get('section', 'N/A')} | "
                                          f"Relevance: {citation.get('relevance_score', 'N/A')}")
                                st.text(citation.get('preview', '')[:200] + "...")
    
    # Chat input
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Conversation", use_container_width=False):
        st.session_state.chat_history = []
        st.session_state.chat_messages = []
        st.rerun()
    
    # Query input
    query = st.chat_input("Ask about the document, search the web, get stock prices, or ask about GDP...")
    
    return query


def add_user_message(query: str):
    """Add user message to chat history.
    
    Args:
        query: User query
    """
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    st.session_state.chat_messages.append({
        'role': 'user',
        'content': query
    })


def add_assistant_message(answer: str, citations: List[Dict] = None, tool_used: str = None, execution_time: float = None):
    """Add assistant message to chat history.
    
    Args:
        answer: Assistant answer
        citations: Optional list of citations
        tool_used: Optional tool name that was used
        execution_time: Optional execution time in seconds
    """
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    st.session_state.chat_messages.append({
        'role': 'assistant',
        'content': answer,
        'citations': citations or [],
        'tool_used': tool_used,
        'execution_time': execution_time
    })
