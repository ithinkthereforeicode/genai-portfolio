# src/job_filter.py
"""
job_filter.py — LLM-based job filtering and scoring.
Uses llm_client.llm_complete() — provider-agnostic (Anthropic/OpenRouter/LMStudio).
Returns FilterResult(kept, skipped) so callers can see what was filtered and why.
"""

import asyncio
import json
import re
from typing import List, Tuple, NamedTuple

from src.models import JobResult, SkippedJob
from src.config import load_track, load_keywords
from src.logger import logger
from src.llm_client import llm_complete


class FilterResult(NamedTuple):
    kept: List[JobResult]
    skipped: List[SkippedJob]


async def _llm_judge(prompt: str) -> str:
    """Call the configured LLM provider via llm_client."""
    logger.log_debug(f"LLM prompt ({len(prompt)} chars): {prompt[:100]}...")
    result = await llm_complete(prompt)
    logger.log_debug(f"LLM response: {result[:200]}")
    return result


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


async def _score_job(jd: str, preferred_keywords: List[str]) -> Tuple[int, str]:
    """
    Score a job 0-100 based on preferred keyword alignment.
    Returns (score, rationale) — rationale explains which criteria drove the score.
    """
    keywords_str = ", ".join(preferred_keywords)
    prompt = f"""Score this job description from 0-100 based on how well it matches these preferred keywords: {keywords_str}

100 = strongly matches most keywords
50 = partial match
0 = no meaningful match

Job description:
\"\"\"
{jd[:2000]}
\"\"\"

Respond with JSON only:
{{"score": <integer 0-100>, "rationale": "2-3 sentences explaining which keywords matched or were missing"}}"""

    try:
        raw = await _llm_judge(prompt)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            score = min(100, max(0, int(data.get("score", 50))))
            rationale = str(data.get("rationale", ""))
            return score, rationale
    except Exception:
        pass
    # fallback: try to parse a bare integer
    try:
        match = re.search(r"\d+", raw)
        if match:
            return min(100, max(0, int(match.group()))), ""
    except Exception:
        pass
    return 50, ""


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

    domain_excludes = [kw.lower() for kw in track.get("keywords", {}).get("domain_exclude", [])]

    for raw in raw_jobs:
        jd = raw.get("description", "")
        title = raw.get("title", "")
        company = raw.get("company", "")

        # Skip jobs with no description — can't score accurately
        if not jd.strip():
            logger.log_llm(f"[{title} @ {company}] SKIP (no description fetched)")
            skipped.append(SkippedJob(
                title=title, company=company,
                url=raw.get("url", ""),
                reason="No job description available (LinkedIn may have blocked the fetch)",
                track=track_name,
            ))
            continue

        # Fast title-level check — no LLM call needed
        title_lower = title.lower()
        title_skip_kw = next((kw for kw in domain_excludes if kw in title_lower), None)
        if title_skip_kw:
            reason = f'Job title contains excluded domain: "{title_skip_kw}"'
            logger.log_llm(f"[{title} @ {company}] SKIP (title filter) — {reason}")
            skipped.append(SkippedJob(
                title=title, company=company,
                url=raw.get("url", ""), reason=reason, track=track_name,
            ))
            continue

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

        score, rationale = await _score_job(jd, preferred)

        # Auto-skip very low scores — clearly irrelevant even if no hard signal
        min_score = track.get("min_score", 20)
        if score < min_score:
            reason = f"Fit score too low ({score}/100 < minimum {min_score}) — {rationale[:120]}"
            logger.log_llm(f"[{title} @ {company}] SKIP (low score={score}) — {rationale[:80]}")
            skipped.append(SkippedJob(
                title=title, company=company,
                url=raw.get("url", ""), reason=reason, track=track_name,
            ))
            continue

        logger.log_llm(f"[{title} @ {company}] KEEP — score={score} | {rationale[:100]}")
        kept.append(JobResult(
            title=title,
            company=company,
            location=raw.get("location", ""),
            posted_date=raw.get("posted_date", ""),
            fit_score=score,
            gaps=[],
            url=raw.get("url", ""),
            track=track_name,
            description=jd[:3000],
            score_rationale=rationale,
        ))

    kept.sort(key=lambda j: j.fit_score, reverse=True)
    return FilterResult(kept=kept, skipped=skipped)
