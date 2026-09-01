"""
save_linkedin_session.py — One-time script to save your LinkedIn session.

Run this ONCE from your terminal:
  cd projects/resume-app
  venv/bin/python scripts/save_linkedin_session.py

A Chrome window opens. Log into LinkedIn normally.
When you see your LinkedIn feed, press Enter in the terminal.
Your session is saved to data/linkedin_session.json and reused by the scraper.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


SESSION_FILE = Path(__file__).parent.parent / "data" / "linkedin_session.json"


async def main():
    print("Opening Chrome — log into LinkedIn, then come back here and press Enter.")
    print()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)  # visible window
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto("https://www.linkedin.com/login")

        input("  → Press Enter once you are logged in and can see your LinkedIn feed: ")

        cookies = await ctx.cookies()
        storage = await ctx.storage_state()

        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(storage, f, indent=2)

        print(f"\n✅ Session saved to {SESSION_FILE}")
        print("   The scraper will now use this session automatically.")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
