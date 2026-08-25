"""LLM factory helper.

Provides a simple interface to create LLM clients for use in nodes.
Students should use this helper so the lab works with any supported provider.

Usage in nodes:
    from .llm import get_llm
    llm = get_llm()
    response = llm.invoke("Hello")
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel


def get_llm(model: str | None = None, temperature: float = 0.0) -> BaseChatModel:
    """Create an LLM client from environment configuration.

    Checks for API keys in this order:
    1. OPENAI_API_KEY → ChatOpenAI
    2. GEMINI_API_KEY → ChatGoogleGenerativeAI
    3. ANTHROPIC_API_KEY → ChatAnthropic

    Override model with the `model` parameter or LLM_MODEL env var.
    """
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    available = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
    }
    if provider and provider not in available:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")
    if provider and not available[provider]:
        raise RuntimeError(f"LLM_PROVIDER={provider} but its API key is not set")
    if not provider:
        provider = next(
            (name for name in ("openai", "gemini", "anthropic") if available[name]),
            "",
        )

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError("Install: pip install langchain-openai") from exc
        return ChatOpenAI(
            model=model or os.getenv("LLM_MODEL") or "gpt-4o-mini",
            temperature=temperature,
        )

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise RuntimeError("Install: pip install langchain-google-genai") from exc
        return ChatGoogleGenerativeAI(
            model=model or os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=temperature,
        )

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise RuntimeError("Install: pip install langchain-anthropic") from exc
        return ChatAnthropic(
            model=model or os.getenv("LLM_MODEL") or "claude-sonnet-4-20250514",
            temperature=temperature,
        )

    raise RuntimeError(
        "No LLM API key found. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY in .env\n"
        "See .env.example for configuration."
    )
