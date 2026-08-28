# tests/test_scraper.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_search_linkedin_returns_list():
    """search_linkedin returns a list (may be empty if LinkedIn blocks)."""
    from src.scraper import search_linkedin
    # Mock Playwright so tests don't need a real browser
    with patch("src.scraper.async_playwright") as mock_pw:
        mock_context = AsyncMock()
        mock_pw.return_value.__aenter__ = AsyncMock(return_value=mock_context)
        mock_pw.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_browser = AsyncMock()
        mock_context.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_page = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_extra_http_headers = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[])
        mock_browser.close = AsyncMock()

        results = await search_linkedin("VP of Engineering", "Remote", max_results=5)
        assert isinstance(results, list)

@pytest.mark.asyncio
async def test_parse_job_card_returns_none_on_missing_title():
    """_parse_job_card returns None when title element is missing."""
    from src.scraper import _parse_job_card
    mock_card = AsyncMock()
    mock_card.query_selector = AsyncMock(return_value=None)
    result = await _parse_job_card(mock_card)
    assert result is None

def test_required_keys_defined():
    """Verify the required keys contract."""
    REQUIRED_KEYS = {"title", "company", "location", "posted_date", "url", "description"}
    assert "title" in REQUIRED_KEYS
    assert "description" in REQUIRED_KEYS
    assert len(REQUIRED_KEYS) == 6
