# src/llm_client.py
"""
llm_client.py — Provider-abstracted LLM completion.
Single entry point: llm_complete(prompt) -> str
Provider selected via LLM_PROVIDER env var: anthropic | openrouter | lmstudio
Falls back to lmstudio if primary provider fails.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Lazy-loaded SDK references
_anthropic_module = None
_openai_module = None


def _get_anthropic_module():
    global _anthropic_module
    if _anthropic_module is None:
        import anthropic
        _anthropic_module = anthropic
    return _anthropic_module


def _get_openai_class():
    global _openai_module
    if _openai_module is None:
        from openai import OpenAI
        _openai_module = OpenAI
    return _openai_module


async def _anthropic_complete(prompt: str, model: str, max_tokens: int) -> str:
    """Call Anthropic API using the anthropic SDK."""
    anthropic = _get_anthropic_module()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key)

    def _sync():
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync)


async def _openai_complete(
    prompt: str, model: str, max_tokens: int, base_url: str, api_key: str
) -> str:
    """Call an OpenAI-compatible API (LM Studio or OpenRouter)."""
    OpenAI = _get_openai_class()
    client = OpenAI(base_url=base_url, api_key=api_key)

    def _sync():
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync)


async def llm_complete(prompt: str) -> str:
    """
    Run a completion with the configured LLM provider.
    Auto-falls back to LM Studio if the primary provider fails.
    """
    from src.config import load_llm_config
    from src.logger import logger

    config = load_llm_config()
    provider = os.environ.get("LLM_PROVIDER", config.get("provider", "lmstudio"))
    model = os.environ.get("FILTER_MODEL", config.get("model", "google/gemma-4-12b-qat"))
    max_tokens = int(config.get("max_tokens", 300))
    fallback_model = config.get("fallback_model", "google/gemma-4-12b-qat")

    try:
        if provider == "anthropic":
            return await _anthropic_complete(prompt, model, max_tokens)
        elif provider == "openrouter":
            return await _openai_complete(
                prompt, model, max_tokens,
                base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            )
        else:  # lmstudio
            return await _openai_complete(
                prompt, model, max_tokens,
                base_url="http://localhost:1234/v1",
                api_key="lm-studio",
            )
    except Exception as e:
        logger.log_event(f"LLM primary provider failed ({provider}): {e} — falling back to LM Studio")
        return await _openai_complete(
            prompt, fallback_model, max_tokens,
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
        )
