# src/job_filter.py
"""
job_filter.py — LLM-based job filtering and scoring.
Returns FilterResult(kept, skipped) so callers can see what was filtered and why.
"""

import asyncio
import json
import os
import re
from typing import List, Tuple, NamedTuple
from dotenv import load_dotenv
from openai import OpenAI

from src.models import JobResult, SkippedJob
from src.config import load_track, load_keywords
from src.logger import logger

load_dotenv()

_client = OpenAI(
    base_url=os.environ.get("OPENROUTER_BASE_URL", "http://localhost:1234/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY", "lm-studio"),
)
_MODEL = os.environ.get("FILTER_MODEL", "google/gemma-4-12b-qat")


class FilterResult(NamedTuple):
    kept: List[JobResult]
    skipped: List[SkippedJob]


def _llm_call(prompt: str) -> str:
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


async def _llm_judge(prompt: str) -> str:
    logger.log_debug(f"LLM prompt ({len(prompt)} chars): {prompt[:100]}...")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _llm_call, prompt)
    logger.log_debug(f"LLM response: {result[:200]}")
    return result


async def should_skip_job(
    jd: str, track: dict, keywords: dict
) -> Tuple[bool, str]:
    citizenship_signals = ", ".join(keywords.get("citizenship_exclude", []))
    domain_excludes = ", ".join(track.get("keywords", {}).get("domain_exclude", []))
    domain_rule = keywords.get("domain_experience_rule", "")

    prompt = f"""You are screening a job description. Answer with JSON only.

Screening rules:
1. SKIP if the JD explicitly requires US citizenship or security clearance. Signals: {citizenship_signals}
2. SKIP if the JD explicitly requires 3+ years of specific domain experience as a hard requirement. Rule: {domain_rule}
3. SKIP if the JD requires deep expertise in these domains: {domain_excludes}
4. A passing mention or "nice to have" does NOT trigger a skip — only hard requirements.

Job description:
\"\"\"
{jd[:2000]}
\"\"\"

Respond with JSON:
{{"skip": true/false, "reason": "one sentence explanation"}}"""

    try:
        raw = await _llm_judge(prompt)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            return bool(data.get("skip", False)), str(data.get("reason", ""))
    except Exception:
        pass
    return False, ""


async def _score_job(jd: str, preferred_keywords: List[str]) -> int:
    keywords_str = ", ".join(preferred_keywords)
    prompt = f"""Score this job description from 0-100 based on how well it matches these preferred keywords: {keywords_str}

100 = strongly matches most keywords
50 = partial match
0 = no meaningful match

Job description:
\"\"\"
{jd[:2000]}
\"\"\"

Respond with a single integer only."""

    try:
        raw = await _llm_judge(prompt)
        match = re.search(r"\d+", raw)
        if match:
            return min(100, max(0, int(match.group())))
    except Exception:
        pass
    return 50


async def filter_jobs(raw_jobs: List[dict], track_name: str) -> FilterResult:
    """
    Filter and score raw job dicts against a track's criteria.
    Returns FilterResult(kept, skipped) — skipped includes the reason for each.
    """
    track = load_track(track_name)
    keywords = load_keywords()
    preferred = track.get("keywords", {}).get("preferred", [])

    kept: List[JobResult] = []
    skipped: List[SkippedJob] = []

    for raw in raw_jobs:
        jd = raw.get("description", "")
        title = raw.get("title", "")
        company = raw.get("company", "")

        skip, reason = await should_skip_job(jd, track, keywords)
        if skip:
            logger.log_llm(f"[{title} @ {company}] SKIP — {reason}")
            skipped.append(SkippedJob(
                title=title,
                company=company,
                url=raw.get("url", ""),
                reason=reason,
                track=track_name,
            ))
            continue

        score = await _score_job(jd, preferred)
        logger.log_llm(f"[{title} @ {company}] KEEP — score={score}")
        kept.append(JobResult(
            title=title,
            company=company,
            location=raw.get("location", ""),
            posted_date=raw.get("posted_date", ""),
            fit_score=score,
            gaps=[],
            url=raw.get("url", ""),
            track=track_name,
        ))

    kept.sort(key=lambda j: j.fit_score, reverse=True)
    return FilterResult(kept=kept, skipped=skipped)
