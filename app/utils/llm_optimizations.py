"""LLM optimizations: KV-caching and speculative decoding."""

import logging
from typing import Optional, Dict, Any
from langchain_core.language_models import BaseChatModel

from app.config.settings import config

logger = logging.getLogger(__name__)


def apply_llm_optimizations(llm: BaseChatModel) -> BaseChatModel:
    """Apply KV-caching and speculative decoding optimizations to LLM.
    
    Args:
        llm: Base LangChain LLM instance
        
    Returns:
        Optimized LLM instance (wrapped or modified)
    """
    if not config.llm_optimization.enabled:
        return llm
    
    # Apply KV-caching
    if config.llm_optimization.kv_cache_enabled:
        llm = _apply_kv_caching(llm)
    
    # Apply speculative decoding
    if config.llm_optimization.speculative_decoding_enabled:
        llm = _apply_speculative_decoding(llm)
    
    logger.info(
        f"Applied LLM optimizations - KV-Cache: {config.llm_optimization.kv_cache_enabled}, "
        f"Speculative Decoding: {config.llm_optimization.speculative_decoding_enabled}"
    )
    
    return llm


def _apply_kv_caching(llm: BaseChatModel) -> BaseChatModel:
    """Apply KV-caching optimization.
    
    KV-caching stores computed key-value pairs from previous tokens,
    avoiding recomputation and speeding up generation.
    
    Note: For custom/LiteLLM endpoints, KV-caching is often automatic
    or may not be supported via explicit parameters. We skip explicit
    configuration for custom endpoints to avoid API errors.
    """
    # Check provider type from config
    is_custom_endpoint = config.llm.provider == "custom"
    
    # Also check if base_url exists (for additional safety)
    has_base_url = hasattr(llm, 'base_url') and getattr(llm, 'base_url', None) is not None
    has_client_base_url = hasattr(llm, 'client') and hasattr(llm.client, 'base_url') and getattr(llm.client, 'base_url', None) is not None
    
    is_custom_endpoint = is_custom_endpoint or has_base_url or has_client_base_url
    
    if is_custom_endpoint:
        # For custom/LiteLLM endpoints, skip explicit KV-caching configuration
        # Most LiteLLM endpoints handle caching automatically, and explicit
        # parameters may not be supported and cause API errors
        # Ensure use_cache is NOT in model_kwargs (remove if present)
        if hasattr(llm, 'model_kwargs') and llm.model_kwargs:
            if 'use_cache' in llm.model_kwargs:
                del llm.model_kwargs['use_cache']
                logger.debug("Removed use_cache from model_kwargs for custom endpoint")
        
        logger.debug("KV-caching: Skipped explicit configuration for custom endpoint (may be automatic)")
    else:
        # For standard OpenAI/Anthropic APIs, use model_kwargs
        if not hasattr(llm, 'model_kwargs') or llm.model_kwargs is None:
            llm.model_kwargs = {}
        llm.model_kwargs['use_cache'] = True
        logger.debug("KV-caching enabled for LLM via model_kwargs (standard API)")
    
    return llm


def _apply_speculative_decoding(llm: BaseChatModel) -> BaseChatModel:
    """Apply speculative decoding optimization.
    
    Speculative decoding uses a smaller "draft" model to generate tokens,
    then a larger "target" model verifies them. This can improve throughput
    by 2-3x while maintaining quality.
    
    Requirements:
    - Draft model (smaller/faster than target)
    - API support for speculative decoding
    - LiteLLM supports this via model parameter or headers
    """
    if not config.llm_optimization.speculative_model:
        logger.warning("Speculative decoding enabled but no speculative_model specified")
        return llm
    
    # Check provider type from config (more reliable than checking attributes)
    is_custom_endpoint = config.llm.provider == "custom"
    
    # Also check if base_url exists (for additional safety)
    has_base_url = hasattr(llm, 'base_url') and getattr(llm, 'base_url', None) is not None
    has_client_base_url = hasattr(llm, 'client') and hasattr(llm.client, 'base_url') and getattr(llm.client, 'base_url', None) is not None
    
    is_custom_endpoint = is_custom_endpoint or has_base_url or has_client_base_url
    
    if is_custom_endpoint:
        # For LiteLLM/custom endpoints, use headers or model name modification
        # Don't add speculative_model to model_kwargs as it causes API errors
        
        # Method 1: Modify model name (for LiteLLM)
        # Format: "target-model?speculative_model=draft-model"
        if hasattr(llm, 'model') and llm.model:
            if '?' not in llm.model:
                llm.model = f"{llm.model}?speculative_model={config.llm_optimization.speculative_model}"
        
        # Method 2: Via custom headers (for LiteLLM)
        if hasattr(llm, 'default_headers'):
            if llm.default_headers is None:
                llm.default_headers = {}
            llm.default_headers['x-speculative-model'] = config.llm_optimization.speculative_model
        
        logger.debug(f"Speculative decoding enabled via headers/model name (custom endpoint): {config.llm_optimization.speculative_model}")
    else:
        # For standard OpenAI/Anthropic APIs, use model_kwargs
        if not hasattr(llm, 'model_kwargs') or llm.model_kwargs is None:
            llm.model_kwargs = {}
        llm.model_kwargs['speculative_model'] = config.llm_optimization.speculative_model
        llm.model_kwargs['speculative_decoding'] = True
        logger.debug(f"Speculative decoding enabled via model_kwargs (standard API): {config.llm_optimization.speculative_model}")
    
    return llm
