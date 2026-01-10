"""Reusable Streamlit UI components."""

import streamlit as st
from typing import Optional


def show_progress(message: str, progress: float):
    """Display progress indicator.
    
    Args:
        message: Progress message
        progress: Progress value (0.0 to 1.0)
    """
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = st.progress(0.0)
        st.session_state.progress_text = st.empty()
    
    st.session_state.progress_bar.progress(progress)
    st.session_state.progress_text.text(f"{message} ({progress:.0%})")


def clear_progress():
    """Clear progress indicators."""
    if 'progress_bar' in st.session_state:
        st.session_state.progress_bar.empty()
        st.session_state.progress_text.empty()
        del st.session_state.progress_bar
        del st.session_state.progress_text


def show_status(message: str, status_type: str = "info"):
    """Display status message.
    
    Args:
        message: Status message
        status_type: Type of status ('info', 'success', 'warning', 'error')
    """
    if status_type == "success":
        st.success(message)
    elif status_type == "warning":
        st.warning(message)
    elif status_type == "error":
        st.error(message)
    else:
        st.info(message)


def styled_button(label: str, key: Optional[str] = None, use_container_width: bool = False):
    """Create a styled button.
    
    Args:
        label: Button label
        key: Optional button key
        use_container_width: Whether to use full width
    """
    return st.button(
        label,
        key=key,
        use_container_width=use_container_width,
        type="primary"
    )
