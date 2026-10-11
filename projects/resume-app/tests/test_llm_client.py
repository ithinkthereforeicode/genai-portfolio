# tests/test_llm_client.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_llm_complete_routes_to_anthropic():
    """When LLM_PROVIDER=anthropic, llm_complete calls _anthropic_complete."""
    with patch.dict("os.environ", {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}):
        with patch("src.llm_client._anthropic_complete", new=AsyncMock(return_value='{"skip": false}')) as mock_fn:
            from src import llm_client
            result = await llm_client.llm_complete("test prompt")
            assert isinstance(result, str)
            mock_fn.assert_called_once()

@pytest.mark.asyncio
async def test_llm_complete_routes_to_lmstudio():
    """When LLM_PROVIDER=lmstudio, llm_complete calls _openai_complete."""
    with patch.dict("os.environ", {"LLM_PROVIDER": "lmstudio"}):
        from src import llm_client
        import importlib
        # Reload BEFORE patching: reloading afterwards redefines _openai_complete
        # and silently discards the mock, causing a live call to localhost:1234.
        importlib.reload(llm_client)
        with patch("src.llm_client._openai_complete", new=AsyncMock(return_value="response")) as mock_fn:
            result = await llm_client.llm_complete("test prompt")
            assert result == "response"
            mock_fn.assert_called_once()

@pytest.mark.asyncio
async def test_llm_complete_fallback_on_error():
    """If primary provider raises, fallback to lmstudio."""
    with patch.dict("os.environ", {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test"}):
        with patch("src.llm_client._anthropic_complete", new=AsyncMock(side_effect=Exception("API error"))):
            with patch("src.llm_client._openai_complete", new=AsyncMock(return_value="fallback")) as mock_fallback:
                from src import llm_client
                result = await llm_client.llm_complete("test prompt")
                assert result == "fallback"
                mock_fallback.assert_called_once()
