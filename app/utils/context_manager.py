"""Context and state management for the application."""

import logging
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
import streamlit as st

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages application context and state persistence."""
    
    def __init__(self, base_path: Path = Path("./context_cache")):
        """Initialize context manager.
        
        Args:
            base_path: Base path for storing context files
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_session_context(self, document_id: str, context: Dict[str, Any]):
        """Save session context to disk.
        
        Args:
            document_id: Document identifier
            context: Context dictionary to save
        """
        try:
            context_file = self.base_path / f"{document_id}_context.json"
            
            # Convert non-serializable objects to metadata
            serializable_context = {}
            for key, value in context.items():
                if key in ['vector_store', 'orchestrator']:
                    # Skip non-serializable objects, they're in session_state
                    continue
                elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    serializable_context[key] = value
                else:
                    serializable_context[key] = str(value)
            
            with open(context_file, 'w') as f:
                json.dump(serializable_context, f, indent=2)
            
            logger.info(f"Saved context for document: {document_id}")
        except Exception as e:
            logger.warning(f"Could not save context: {str(e)}")
    
    def load_session_context(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Load session context from disk.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Context dictionary or None if not found
        """
        try:
            context_file = self.base_path / f"{document_id}_context.json"
            if context_file.exists():
                with open(context_file, 'r') as f:
                    context = json.load(f)
                logger.info(f"Loaded context for document: {document_id}")
                return context
        except Exception as e:
            logger.warning(f"Could not load context: {str(e)}")
        return None
    
    @staticmethod
    def get_session_state_summary() -> Dict[str, Any]:
        """Get summary of current session state.
        
        Returns:
            Dictionary with session state summary
        """
        summary = {
            'document_uploaded': st.session_state.get('document_uploaded', False),
            'document_id': st.session_state.get('document_id'),
            'has_vector_store': st.session_state.get('vector_store') is not None,
            'has_orchestrator': st.session_state.get('orchestrator') is not None,
            'has_kpi_report': st.session_state.get('kpi_report') is not None,
            'chat_history_length': len(st.session_state.get('chat_history', [])),
            'chat_messages_length': len(st.session_state.get('chat_messages', [])),
        }
        return summary
