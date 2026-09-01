# src/scraper.py
"""
scraper.py — LinkedIn job search via Playwright browser automation.
Two-phase scraping:
  Phase 1: scrape_job_cards()  — get all cards (title, company, url) from search page
  Phase 2: fetch_descriptions() — visit only the jobs that pass the title filter
This minimises LinkedIn page loads and avoids rate limiting.
"""

import asyncio
import random
from pathlib import Path
from typing import List, Optional
from playwright.async_api import async_playwright, Page

from src.logger import logger

SESSION_FILE = Path(__file__).parent.parent / "data" / "linkedin_session.json"


def _load_session() -> Optional[dict]:
    """Load saved LinkedIn session state if available."""
    if SESSION_FILE.exists():
        import json
        with open(SESSION_FILE) as f:
            return json.load(f)
    return None


def _screenshot_dir(run_id: str) -> Optional[Path]:
    if not run_id:
        return None
    base = Path(__file__).parent.parent / "data" / "screenshots" / run_id
    base.mkdir(parents=True, exist_ok=True)
    return base


async def _random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _parse_job_card(card) -> Optional[dict]:
    """Extract job metadata from a LinkedIn search card. No description yet."""
    try:
        title_el  = await card.query_selector(".job-card-list__title, .base-search-card__title")
        company_el = await card.query_selector(".job-card-container__primary-description, .base-search-card__subtitle")
        location_el = await card.query_selector(".job-card-container__metadata-item, .job-search-card__location")
        link_el   = await card.query_selector("a.job-card-list__title, a.base-card__full-link")
        time_el   = await card.query_selector("time")

        if not title_el or not link_el:
            return None

        return {
            "title":       (await title_el.inner_text()).strip(),
            "company":     (await company_el.inner_text()).strip() if company_el else "Unknown",
            "location":    (await location_el.inner_text()).strip() if location_el else "Unknown",
            "posted_date": await time_el.get_attribute("datetime") if time_el else "",
            "url":         await link_el.get_attribute("href") or "",
            "description": "",
        }
    except Exception:
        return None


async def _fetch_one_description(page: Page, url: str) -> str:
    """Navigate to a job page and return the description text."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await _random_delay(2.0, 4.0)

        for selector in [
            ".show-more-less-html__markup",
            ".description__text",
            ".description__text--rich",
            ".jobs-description-content__text",
            "#job-details",
        ]:
            el = await page.query_selector(selector)
            if el:
                text = (await el.inner_text()).strip()
                if len(text) > 50:
                    return text

        # Detect login wall
        body = await page.inner_text("body")
        if "Sign in" in body and len(body) < 2000:
            logger.log_debug(f"LinkedIn login wall hit: {url}")
    except Exception as e:
        logger.log_debug(f"Description fetch failed for {url}: {e}")
    return ""


async def scrape_job_cards(
    query: str,
    location: str = "United States",
    max_results: int = 60,
    max_days: int = 1,
    run_id: str = "",
) -> List[dict]:
    """
    Phase 1 — Scrape job cards from LinkedIn search results.
    Returns list of dicts with title, company, location, posted_date, url.
    No descriptions yet (fast, single page load).
    """
    results = []
    f_tpr = f"r{max_days * 86400}"
    search_url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={query.replace(' ', '%20')}"
        f"&location={location.replace(' ', '%20')}"
        f"&f_WT=2"
        f"&f_TPR={f_tpr}"
        f"&sortBy=DD"
    )
    screenshot_dir = _screenshot_dir(run_id)
    logger.log_debug(f"LinkedIn URL: {search_url}")

    session = _load_session()
    if session:
        logger.log_debug("Using saved LinkedIn session (authenticated)")
    else:
        logger.log_debug("No LinkedIn session found — running as anonymous (limited results)")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            storage_state=session if session else None,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await _random_delay(2.0, 4.0)

            if screenshot_dir:
                await page.screenshot(path=str(screenshot_dir / "01-search-results.png"))

            cards = await page.query_selector_all(".job-card-list__entity-lockup, .base-card")
            logger.log_debug(f"Found {len(cards)} cards on search page")

            for card in cards[:max_results]:
                job = await _parse_job_card(card)
                if job:
                    results.append(job)
                await _random_delay(0.3, 0.8)

        except Exception as e:
            logger.log_debug(f"Search page scrape error: {e}")
        finally:
            await browser.close()

    logger.log_debug(f"Scraped {len(results)} job cards")
    return results


async def fetch_descriptions(
    jobs: List[dict],
    run_id: str = "",
    max_concurrent: int = 1,
) -> List[dict]:
    """
    Phase 2 — Fetch full job descriptions for a filtered list of jobs.
    Visits each job URL individually. Mutates and returns the list.
    Only call this AFTER title filtering — minimises LinkedIn page loads.
    """
    screenshot_dir = _screenshot_dir(run_id)

    session = _load_session()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            storage_state=session if session else None,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

        try:
            for i, job in enumerate(jobs):
                if not job.get("url"):
                    continue
                logger.log_debug(f"Fetching description ({i+1}/{len(jobs)}): {job['title']} @ {job['company']}")
                job["description"] = await _fetch_one_description(page, job["url"])

                if screenshot_dir and i == 0:
                    await page.screenshot(path=str(screenshot_dir / "02-first-job-detail.png"))

        except Exception as e:
            logger.log_debug(f"Description batch error: {e}")
        finally:
            await browser.close()

    fetched = sum(1 for j in jobs if j.get("description"))
    logger.log_debug(f"Descriptions fetched: {fetched}/{len(jobs)}")
    return jobs


# ── Convenience wrapper (backwards-compatible) ────────────────────────────────

async def search_linkedin(
    query: str,
    location: str = "United States",
    max_results: int = 60,
    headless: bool = True,
    run_id: str = "",
    max_days: int = 1,
) -> List[dict]:
    """Legacy single-phase search (cards + descriptions). Use two-phase via job_picker."""
    jobs = await scrape_job_cards(query, location, max_results, max_days, run_id)
    jobs = await fetch_descriptions(jobs, run_id)
    return jobs
