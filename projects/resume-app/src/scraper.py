# src/scraper.py
"""
scraper.py — LinkedIn job search via Playwright browser automation.
Uses headless Chromium. Adds human-like delays to avoid rate limiting.
Captures screenshots at key navigation steps for observability.
"""

import asyncio
import random
from pathlib import Path
from typing import List, Optional
from playwright.async_api import async_playwright, Page

from src.logger import logger


def _screenshot_dir(run_id: str) -> Optional[Path]:
    if not run_id:
        return None
    base = Path(__file__).parent.parent / "data" / "screenshots" / run_id
    base.mkdir(parents=True, exist_ok=True)
    return base


async def _random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Human-like delay between actions."""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _parse_job_card(card) -> Optional[dict]:
    """Extract job data from a LinkedIn job card element. Returns None if parsing fails."""
    try:
        title_el = await card.query_selector(".job-card-list__title, .base-search-card__title")
        company_el = await card.query_selector(".job-card-container__primary-description, .base-search-card__subtitle")
        location_el = await card.query_selector(".job-card-container__metadata-item, .job-search-card__location")
        link_el = await card.query_selector("a.job-card-list__title, a.base-card__full-link")
        time_el = await card.query_selector("time")

        if not title_el or not link_el:
            return None

        title = (await title_el.inner_text()).strip()
        company = (await company_el.inner_text()).strip() if company_el else "Unknown"
        location = (await location_el.inner_text()).strip() if location_el else "Unknown"
        url = await link_el.get_attribute("href") or ""
        posted_date = await time_el.get_attribute("datetime") if time_el else ""

        return {
            "title": title,
            "company": company,
            "location": location,
            "posted_date": posted_date,
            "url": url,
            "description": "",
        }
    except Exception:
        return None


async def _get_job_description(page: Page, url: str) -> str:
    """Navigate to a job page and extract the description."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await _random_delay(2.0, 4.0)  # longer delay to avoid throttle

        # Try multiple selectors — LinkedIn varies by page type
        for selector in [
            ".show-more-less-html__markup",
            ".description__text",
            ".description__text--rich",
            ".jobs-description-content__text",
            "#job-details",
        ]:
            desc_el = await page.query_selector(selector)
            if desc_el:
                text = (await desc_el.inner_text()).strip()
                if len(text) > 50:   # ignore tiny/empty matches
                    return text

        # Fallback: check if we hit a login wall
        page_text = await page.inner_text("body")
        if "Sign in" in page_text and len(page_text) < 2000:
            logger.log_debug(f"LinkedIn login wall hit for: {url}")
    except Exception as e:
        logger.log_debug(f"Description fetch failed for {url}: {e}")
    return ""


async def search_linkedin(
    query: str,
    location: str = "United States",
    max_results: int = 20,
    headless: bool = True,
    run_id: str = "",
    max_days: int = 7,
) -> List[dict]:
    """
    Search LinkedIn for jobs matching query and location.
    Returns list of raw job dicts with keys:
      title, company, location, posted_date, url, description
    Captures screenshots when run_id is provided.
    max_days: only return jobs posted within this many days (LinkedIn f_TPR filter).
    """
    results = []
    f_tpr = f"r{max_days * 86400}"   # LinkedIn: seconds since posting
    search_url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={query.replace(' ', '%20')}"
        f"&location={location.replace(' ', '%20')}"
        f"&f_WT=2"
        f"&f_TPR={f_tpr}"
        f"&sortBy=DD"
    )
    screenshot_dir = _screenshot_dir(run_id)

    logger.log_debug(f"Playwright launching headless Chromium")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page()

        await page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        try:
            logger.log_debug(f"Navigating to: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await _random_delay(2.0, 4.0)

            if screenshot_dir:
                screenshot_path = str(screenshot_dir / "01-search-results.png")
                await page.screenshot(path=screenshot_path)
                logger.log_debug(f"Screenshot saved: 01-search-results.png")

            cards = await page.query_selector_all(
                ".job-card-list__entity-lockup, .base-card"
            )
            logger.log_debug(f"Found {len(cards)} job cards on page")

            for card in cards[:max_results]:
                job = await _parse_job_card(card)
                if job:
                    results.append(job)
                await _random_delay(0.5, 1.5)

            # Fetch descriptions for all results (needed for accurate LLM filtering)
            desc_page = await browser.new_page()
            for i, job in enumerate(results):
                if job["url"]:
                    logger.log_debug(f"Fetching description for: {job['title']} @ {job['company']}")
                    job["description"] = await _get_job_description(desc_page, job["url"])
                    if screenshot_dir and i == 0:
                        screenshot_path = str(screenshot_dir / "02-first-job-detail.png")
                        await desc_page.screenshot(path=screenshot_path)
                        logger.log_debug(f"Screenshot saved: 02-first-job-detail.png")
                    await _random_delay(1.5, 3.0)
            await desc_page.close()

        except Exception as e:
            logger.log_debug(f"Scraper error: {e}")
        finally:
            await browser.close()

    return results
