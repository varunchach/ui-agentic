"""Application configuration and settings management."""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from app.config.utils import get_bool_env, get_int_env, get_float_env

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMConfig:
    """LLM provider configuration."""
    
    def __init__(self):
        self.provider = self._detect_provider()
        self.api_key = self._get_api_key()
        self.model = self._get_model()
        self.temperature = get_float_env(
            "CUSTOM_LLM_TEMPERATURE",
            get_float_env("OPENAI_TEMPERATURE", get_float_env("ANTHROPIC_TEMPERATURE", 0.0))
        )
        self.endpoint = os.getenv("CUSTOM_LLM_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
    def _detect_provider(self) -> str:
        """Detect which LLM provider is configured."""
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        elif os.getenv("AZURE_OPENAI_API_KEY"):
            return "azure"
        elif os.getenv("CUSTOM_LLM_ENDPOINT"):
            return "custom"
        else:
            raise ValueError(
                "No LLM provider configured. Please set one of: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_API_KEY, or CUSTOM_LLM_ENDPOINT"
            )
    
    def _get_api_key(self) -> str:
        """Get API key for the configured provider."""
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == "azure":
            return os.getenv("AZURE_OPENAI_API_KEY")
        elif self.provider == "custom":
            return os.getenv("CUSTOM_LLM_API_KEY", "")
        return ""
    
    def _get_model(self) -> str:
        """Get model name for the configured provider."""
        if self.provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        elif self.provider == "azure":
            return os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        elif self.provider == "custom":
            return os.getenv("CUSTOM_LLM_MODEL", "llama2")
        return ""


class EmbeddingConfig:
    """Embedding model configuration."""
    
    def __init__(self):
        # Default to fast, lightweight embedding model
        # Options: 
        # - "sentence-transformers/all-MiniLM-L6-v2" (fastest, 384 dim)
        # - "sentence-transformers/all-mpnet-base-v2" (balanced, 768 dim)
        # - "BAAI/bge-small-en-v1.5" (fast, 384 dim, good quality)
        # - "nomic-ai/nomic-embed-text-v1.5" (slower but high quality, 768 dim)
        self.model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        # Auto-detect dimension based on model
        model_dim_map = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "bge-small": 384,
            "bge-base": 768,
            "nomic-embed-text": 768,
        }
        default_dim = 384  # Safe default for most small models
        for key, dim in model_dim_map.items():
            if key in self.model.lower():
                default_dim = dim
                break
        self.dimension = get_int_env("EMBEDDING_DIMENSION", default_dim)


class VectorStoreConfig:
    """Vector store configuration."""
    
    def __init__(self):
        self.index_path = Path(os.getenv("FAISS_INDEX_PATH", "./vector_store/faiss_index"))
        self.store_path = Path(os.getenv("VECTOR_STORE_PATH", "./vector_store"))
        
        # Create directories if they don't exist
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)


class RerankerConfig:
    """Re-ranker configuration."""
    
    def __init__(self):
        self.model = os.getenv("BGE_RERANKER_MODEL", "BAAI/bge-large-en-v1.5")
        self.top_k = get_int_env("RERANKER_TOP_K", 10)
        # Optional: Hugging Face token for better rate limits (not required for public models)
        self.hf_token = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")


class ChunkingConfig:
    """Chunking configuration."""
    
    def __init__(self):
        self.chunk_size = get_int_env("CHUNK_SIZE", 1000)
        self.chunk_overlap = get_int_env("CHUNK_OVERLAP", 200)
        self.section_aware = get_bool_env("ENABLE_SECTION_AWARE_CHUNKING", True)


class RetrievalConfig:
    """Retrieval configuration."""
    
    def __init__(self):
        self.top_k = get_int_env("RETRIEVAL_TOP_K", 20)
        self.rerank_top_k = get_int_env("RERANK_TOP_K", 5)


class LLMOptimizationConfig:
    """LLM optimization configuration (KV-caching, speculative decoding)."""
    
    def __init__(self):
        self.enabled = get_bool_env("LLM_OPTIMIZATION_ENABLED", True)
        self.kv_cache_enabled = get_bool_env("KV_CACHE_ENABLED", True)
        self.speculative_decoding_enabled = get_bool_env("SPECULATIVE_DECODING_ENABLED", True)  # Enabled by default
        # Draft model for speculative decoding (should be smaller/faster than main model)
        self.speculative_model = os.getenv("SPECULATIVE_MODEL", "")
        
        if self.speculative_decoding_enabled and not self.speculative_model:
            logger.warning(
                "Speculative decoding enabled but no speculative_model specified. "
                "Speculative decoding will be disabled."
            )
            self.speculative_decoding_enabled = False


class AppConfig:
    """Main application configuration."""
    
    def __init__(self):
        self.llm = LLMConfig()
        self.embedding = EmbeddingConfig()
        self.vector_store = VectorStoreConfig()
        self.reranker = RerankerConfig()
        self.chunking = ChunkingConfig()
        self.retrieval = RetrievalConfig()
        self.llm_optimization = LLMOptimizationConfig()
        self.max_file_size_mb = get_int_env("MAX_FILE_SIZE_MB", 50)
        
        logger.info(f"Configuration loaded - LLM Provider: {self.llm.provider}, Model: {self.llm.model}")
        if self.llm_optimization.enabled:
            logger.info(
                f"LLM Optimizations - KV-Cache: {self.llm_optimization.kv_cache_enabled}, "
                f"Speculative Decoding: {self.llm_optimization.speculative_decoding_enabled}"
            )


# Global configuration instance
config = AppConfig()
