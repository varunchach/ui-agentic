"""Utility functions for configuration."""

import os
from typing import Any


def get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean value from environment variable.
    
    Args:
        key: Environment variable name
        default: Default boolean value if not set
        
    Returns:
        Boolean value
    """
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_int_env(key: str, default: int) -> int:
    """Get integer value from environment variable.
    
    Args:
        key: Environment variable name
        default: Default integer value if not set
        
    Returns:
        Integer value
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_float_env(key: str, default: float) -> float:
    """Get float value from environment variable.
    
    Args:
        key: Environment variable name
        default: Default float value if not set
        
    Returns:
        Float value
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default
