"""Main Streamlit UI application."""

import streamlit as st
import hashlib
from pathlib import Path
import logging

from app.ingestion.pipeline import IngestionPipeline
from app.agents.orchestrator import AgentOrchestrator
from app.ui.components import show_progress, clear_progress, show_status, styled_button
from app.ui.kpi_report_view import render_kpi_report
from app.ui.chat_view import render_chat_interface, add_user_message, add_assistant_message

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="BFSI Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)


def get_document_id(file_name: str, file_content: bytes) -> str:
    """Generate unique document ID from file."""
    content_hash = hashlib.md5(file_content).hexdigest()
    return f"{Path(file_name).stem}_{content_hash[:8]}"


def progress_callback(message: str, progress: float):
    """Progress callback for ingestion pipeline."""
    show_progress(message, progress)


def initialize_session_state():
    """Initialize Streamlit session state variables.
    
    Context is automatically saved in Streamlit's session_state which persists
    during the session. The following variables are maintained:
    
    - document_uploaded: Whether document has been ingested
    - document_id: Unique identifier for the current document
    - vector_store: FAISS vector store instance (in memory)
    - orchestrator: Agent orchestrator instance (in memory)
    - kpi_report: Generated KPI report content
    - kpi_data: Extracted KPI data dictionary
    - chat_history: Conversation history for chat flow
    - chat_messages: UI messages for chat display
    """
    if 'document_uploaded' not in st.session_state:
        st.session_state.document_uploaded = False
    
    if 'document_id' not in st.session_state:
        st.session_state.document_id = None
    
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    
    if 'kpi_report' not in st.session_state:
        st.session_state.kpi_report = None
    
    if 'kpi_data' not in st.session_state:
        st.session_state.kpi_data = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []


def main():
    """Main application function."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">📄 BFSI Document Intelligence Chatbot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload a BFSI document to extract KPIs or chat with the document</div>', unsafe_allow_html=True)
    
    # Capabilities section
    with st.expander("🤖 What This Bot Can Do", expanded=False):
        st.markdown("""
        ### 📊 Document Intelligence
        - **KPI Extraction**: Automatically extract financial KPIs (Revenue, Profit, ROE, ROA, GNPA, NNPA, PCR, CRAR/CAR)
        - **Report Generation**: Generate comprehensive BFSI reports with executive summaries
        - **Document Q&A**: Ask questions about uploaded documents with citations
        
        ### 🔧 External Tools & Real-Time Data
        - **Web Search**: Search the web for current information, news, and events
        - **Stock Market Data**: Get real-time stock prices, market data using yfinance
        - **Economic Indicators**: Access GDP data and economic indicators for countries
        
        ### 🧠 Agentic Intelligence
        - **Smart Routing**: Automatically decides whether to use document RAG or external tools
        - **Combined Answers**: Can combine document information with real-time data
        - **Context-Aware**: Maintains conversation memory and document context
        """)
        
        st.markdown("**Example Queries:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - "What is the revenue in the document?"
            - "Compare GNPA with industry average"
            - "What does the report say about CRAR?"
            """)
        with col2:
            st.markdown("""
            - "What is the current price of AAPL?"
            - "Search for latest banking regulations"
            - "What is the GDP of India?"
            """)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Document Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'txt', 'docx', 'doc'],
            help="Upload a BFSI document (PDF, TXT, or DOCX)"
        )
        
        if uploaded_file is not None:
            # Check if this is a new document
            file_content = uploaded_file.read()
            doc_id = get_document_id(uploaded_file.name, file_content)
            
            # Check if document already ingested
            if st.session_state.document_id != doc_id:
                st.session_state.document_id = doc_id
                st.session_state.document_uploaded = False
                st.session_state.vector_store = None
                st.session_state.orchestrator = None
                st.session_state.kpi_report = None
                st.session_state.kpi_data = None
                st.session_state.chat_history = []
                st.session_state.chat_messages = []
            
            # Ingestion
            if not st.session_state.document_uploaded:
                if st.button("📥 Ingest Document", use_container_width=True, type="primary"):
                    try:
                        # Use empty() to create a placeholder for status updates
                        status_placeholder = st.empty()
                        status_placeholder.info("🔄 Starting ingestion... This may take a few minutes for large documents.")
                        
                        # Initialize pipeline
                        pipeline = IngestionPipeline(progress_callback=progress_callback)
                        
                        # Ingest document with better error handling
                        try:
                            vector_store = pipeline.ingest(
                                file_path=uploaded_file.name,
                                file_content=file_content,
                                document_id=doc_id
                            )
                        except MemoryError:
                            clear_progress()
                            status_placeholder.error("❌ Out of memory during ingestion. The document may be too large. Try a smaller document or increase pod memory limits.")
                            logger.error("Memory error during ingestion")
                            st.stop()
                        except Exception as ingest_error:
                            clear_progress()
                            status_placeholder.error(f"❌ Ingestion failed: {str(ingest_error)}")
                            logger.error(f"Ingestion error: {str(ingest_error)}", exc_info=True)
                            st.stop()
                        
                        # Store in session state
                        st.session_state.vector_store = vector_store
                        st.session_state.document_uploaded = True
                        
                        # Initialize orchestrator
                        try:
                            orchestrator = AgentOrchestrator(vector_store)
                            st.session_state.orchestrator = orchestrator
                        except Exception as orch_error:
                            clear_progress()
                            status_placeholder.error(f"❌ Failed to initialize orchestrator: {str(orch_error)}")
                            logger.error(f"Orchestrator initialization error: {str(orch_error)}", exc_info=True)
                            st.stop()
                        
                        clear_progress()
                        status_placeholder.success("✅ Document ingested successfully!")
                        logger.info(f"Document {uploaded_file.name} ingested successfully")
                        st.rerun()
                            
                    except Exception as e:
                        clear_progress()
                        show_status(f"❌ Unexpected error during ingestion: {str(e)}", "error")
                        logger.error(f"Unexpected ingestion error: {str(e)}", exc_info=True)
            else:
                show_status("✅ Document ready", "success")
                st.info(f"Document: {uploaded_file.name}")
    
    # Main content area
    if not st.session_state.document_uploaded:
        st.info("👆 Please upload and ingest a document to get started.")
        return
    
    # Two-button interface
    st.markdown("---")
    st.subheader("🚀 Choose Your Workflow")
    
    col1, col2 = st.columns(2)
    
    with col1:
        generate_kpi = styled_button(
            "📊 Generate KPI Report",
            key="btn_kpi",
            use_container_width=True
        )
    
    with col2:
        chat_doc = styled_button(
            "💬 Chat with Document",
            key="btn_chat",
            use_container_width=True
        )
    
    # Handle KPI Report flow
    if generate_kpi:
        if st.session_state.orchestrator is None:
            show_status("❌ Orchestrator not initialized", "error")
            return
        
        try:
            with st.spinner("Generating KPI report..."):
                result = st.session_state.orchestrator.execute("kpi_report")
                
                st.session_state.kpi_report = result.get("report")
                st.session_state.kpi_data = result.get("kpi_data")
                st.session_state.kpi_execution_time = result.get("execution_time")
                
                st.rerun()
                
        except Exception as e:
            show_status(f"❌ Error generating report: {str(e)}", "error")
            logger.error(f"KPI report error: {str(e)}", exc_info=True)
    
    # Handle Chat flow
    if chat_doc:
        st.session_state.current_view = "chat"
        st.rerun()
    
    # Display KPI Report if available
    if st.session_state.kpi_report:
        st.markdown("---")
        render_kpi_report(
            st.session_state.kpi_report,
            st.session_state.kpi_data or {},
            st.session_state.get('kpi_execution_time')
        )
    
    # Display Chat interface if selected
    if st.session_state.get('current_view') == "chat" or chat_doc:
        st.markdown("---")
        query = render_chat_interface()
        
        if query:
            if st.session_state.orchestrator is None:
                show_status("❌ Orchestrator not initialized", "error")
                return
            
            # Add user message
            add_user_message(query)
            
            try:
                with st.spinner("Thinking..."):
                    # Get chat history
                    chat_history = st.session_state.get('chat_history', [])
                    
                    # Execute chat flow
                    result = st.session_state.orchestrator.execute(
                        "chat",
                        query=query,
                        chat_history=chat_history
                    )
                    
                    answer = result.get("answer", "Not available in the document.")
                    citations = result.get("citations", [])
                    tool_used = result.get("tool_used")
                    execution_time = result.get("execution_time")
                    updated_history = result.get("chat_history", [])
                    
                    # Update session state
                    st.session_state.chat_history = updated_history
                    
                    # Add assistant message with execution time
                    add_assistant_message(answer, citations, tool_used, execution_time)
                    
                    st.rerun()
                    
            except Exception as e:
                show_status(f"❌ Error generating answer: {str(e)}", "error")
                logger.error(f"Chat error: {str(e)}", exc_info=True)
                add_assistant_message("Sorry, I encountered an error. Please try again.")


if __name__ == "__main__":
    main()
