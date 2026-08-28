# src/job_filter.py
"""
job_filter.py — LLM-based job filtering and scoring.
Applies the decision logic from the spec:
  1. LLM judgment calls (citizenship, domain experience)
  2. Keyword scoring — LLM guided by preferred keywords
"""

import os
import json
import asyncio
import re
from typing import List, Tuple
from dotenv import load_dotenv
from openai import OpenAI

from src.models import JobResult
from src.config import load_track, load_keywords

load_dotenv()

_client = OpenAI(
    base_url=os.environ.get("OPENROUTER_BASE_URL", "http://localhost:1234/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY", "lm-studio"),
)
_MODEL = os.environ.get("FILTER_MODEL", "google/gemma-4-12b-qat")


def _llm_call(prompt: str) -> str:
    """Synchronous LLM call."""
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


async def _llm_judge(prompt: str) -> str:
    """Run LLM call in thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _llm_call, prompt)


async def should_skip_job(
    jd: str, track: dict, keywords: dict
) -> Tuple[bool, str]:
    """
    LLM judgment: should this job be skipped?
    Returns (should_skip, reason).
    """
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
    """Score a job 0-100 based on preferred keyword alignment."""
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


async def filter_jobs(raw_jobs: List[dict], track_name: str) -> List[JobResult]:
    """
    Filter and score raw job dicts against a track's criteria.
    Returns a list of JobResult objects, sorted by fit_score descending.
    """
    track = load_track(track_name)
    keywords = load_keywords()
    preferred = track.get("keywords", {}).get("preferred", [])

    results = []
    for raw in raw_jobs:
        jd = raw.get("description", "")

        skip, reason = await should_skip_job(jd, track, keywords)
        if skip:
            continue

        score = await _score_job(jd, preferred)

        results.append(JobResult(
            title=raw.get("title", ""),
            company=raw.get("company", ""),
            location=raw.get("location", ""),
            posted_date=raw.get("posted_date", ""),
            fit_score=score,
            gaps=[],
            url=raw.get("url", ""),
            track=track_name,
        ))

    results.sort(key=lambda j: j.fit_score, reverse=True)
    return results
