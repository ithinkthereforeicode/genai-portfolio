# src/scraper.py
"""
scraper.py — LinkedIn job search via Playwright browser automation.
Uses headless Chromium. Adds human-like delays to avoid rate limiting.
"""

import asyncio
import random
from typing import List, Optional
from playwright.async_api import async_playwright, Page


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
            "description": "",  # fetched separately in _get_job_description()
        }
    except Exception:
        return None


async def _get_job_description(page: Page, url: str) -> str:
    """Navigate to a job page and extract the description."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await _random_delay(1.0, 2.0)
        desc_el = await page.query_selector(".description__text, .show-more-less-html__markup")
        if desc_el:
            return (await desc_el.inner_text()).strip()
    except Exception:
        pass
    return ""


async def search_linkedin(
    query: str,
    location: str = "United States",
    max_results: int = 20,
    headless: bool = True,
) -> List[dict]:
    """
    Search LinkedIn for jobs matching query and location.
    Returns list of raw job dicts with keys:
      title, company, location, posted_date, url, description
    """
    results = []
    search_url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={query.replace(' ', '%20')}"
        f"&location={location.replace(' ', '%20')}"
        f"&f_WT=2"
        f"&sortBy=DD"
    )

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
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await _random_delay(2.0, 4.0)

            cards = await page.query_selector_all(
                ".job-card-list__entity-lockup, .base-card"
            )

            for card in cards[:max_results]:
                job = await _parse_job_card(card)
                if job:
                    results.append(job)
                await _random_delay(0.5, 1.5)

            # Fetch descriptions for top results
            desc_page = await browser.new_page()
            for job in results[:10]:
                if job["url"]:
                    job["description"] = await _get_job_description(desc_page, job["url"])
                    await _random_delay(1.5, 3.0)
            await desc_page.close()

        except Exception:
            pass
        finally:
            await browser.close()

    return results
