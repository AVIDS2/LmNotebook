"""
LLM integration using Universal OpenAI Protocol.
Supports switching between any provider (DeepSeek, Gemini, OpenAI, etc.) via configuration.
"""
import os
import httpx
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from core.config import settings
from core.model_manager import model_manager


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))


# Global client instance
_llm: ChatOpenAI = None


def get_llm(model: Optional[str] = None) -> ChatOpenAI:
    """
    Get a universal LLM instance using OpenAI protocol.
    Bypasses system proxy for both sync and async calls to ensure stability.
    """
    global _llm
    
    # Try to get active provider from manager
    active_provider = model_manager.get_active_provider()
    
    # Fallback to defaults from settings if manager somehow fails
    api_key = active_provider.get("apiKey") if active_provider else settings.OPENAI_API_KEY
    base_url = active_provider.get("baseUrl") if active_provider else settings.OPENAI_BASE_URL
    target_model = model or (active_provider.get("modelName") if active_provider else settings.MODEL_NAME)

    # Use a cache key based on the current configuration to detect changes
    config_hash = f"{base_url}_{target_model}_{api_key[-4:] if api_key else ''}"
    
    # Cache the instance if config hasn't changed
    if _llm is not None and model is None and getattr(_llm, "_origin_config_hash", None) == config_hash:
        return _llm
        
    # We create both sync and async clients to ensure proxy bypass
    # Use Timeout object for granular control - streaming needs longer read timeout
    timeout_config = httpx.Timeout(
        connect=30.0,    # Connection timeout
        read=120.0,      # Read timeout (longer for streaming)
        write=30.0,      # Write timeout
        pool=30.0        # Pool timeout
    )
    sync_client = httpx.Client(trust_env=False, verify=True, timeout=timeout_config)
    async_client = httpx.AsyncClient(trust_env=False, verify=True, timeout=timeout_config)

    llm = ChatOpenAI(
        model=target_model,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=0.7,
        max_tokens=4096,
        streaming=True,
        http_client=sync_client,
        http_async_client=async_client
    )
    
    # Tag the instance for cache invalidation
    setattr(llm, "_origin_config_hash", config_hash)
    
    if model is None:
        _llm = llm
        
    safe_print(f"[OK] LLM configured ({active_provider['name'] if active_provider else 'Default'}): {target_model}")
    return llm


def get_grading_llm() -> ChatOpenAI:
    """Get LLM for internal tasks."""
    return get_llm()
