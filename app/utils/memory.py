"""Conversation memory management for chat flow."""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history for chat sessions."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize conversation memory.
        
        Args:
            session_id: Optional session identifier
        """
        self.session_id = session_id
        self.history: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        self.history.append({
            "role": role,
            "content": content
        })
        logger.debug(f"Added {role} message to history (total: {len(self.history)})")
    
    def get_history(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history.
        
        Args:
            max_messages: Optional limit on number of messages to return
            
        Returns:
            List of message dictionaries
        """
        if max_messages:
            return self.history[-max_messages:]
        return self.history.copy()
    
    def clear(self):
        """Clear conversation history."""
        self.history = []
        logger.info("Cleared conversation history")
    
    def get_last_n_exchanges(self, n: int = 5) -> List[Dict[str, str]]:
        """Get last N message exchanges (user + assistant pairs).
        
        Args:
            n: Number of exchanges to return
            
        Returns:
            List of message dictionaries
        """
        return self.history[-(n * 2):] if len(self.history) > n * 2 else self.history
