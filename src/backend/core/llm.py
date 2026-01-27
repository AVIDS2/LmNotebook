"""
LLM integration using Universal OpenAI Protocol.
Supports switching between any provider (DeepSeek, Gemini, OpenAI, etc.) via configuration.
"""
import os
import httpx
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from core.config import settings


# Global client instance
_llm: ChatOpenAI = None


def get_llm(model: Optional[str] = None) -> ChatOpenAI:
    """
    Get a universal LLM instance using OpenAI protocol.
    Bypasses system proxy for both sync and async calls to ensure stability.
    """
    global _llm
    
    # Cache the instance if using the default model
    if _llm is not None and model is None:
        return _llm
        
    target_model = model or settings.MODEL_NAME
    
    # We create both sync and async clients to ensure proxy bypass in all scenarios
    # 502 errors often occur when async calls try to go through a system proxy intended for external traffic
    sync_client = httpx.Client(trust_env=False, verify=True, timeout=60.0)
    async_client = httpx.AsyncClient(trust_env=False, verify=True, timeout=60.0)

    llm = ChatOpenAI(
        model=target_model,
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=0.7,
        max_tokens=2048,
        streaming=True,  # CRITICAL: Enable true streaming
        http_client=sync_client,
        http_async_client=async_client
    )
    
    if model is None:
        _llm = llm
        
    print(f"✅ LLM configured (Universal Protocol): {target_model}")
    print(f"🔗 API Base: {settings.OPENAI_BASE_URL}")
    
    return llm


def get_grading_llm() -> ChatOpenAI:
    """Get LLM for internal tasks."""
    return get_llm()
