# src/models.py
from dataclasses import dataclass, field
from typing import List, Literal, Optional

TriggeredBy = Literal["ui", "schedule", "claude-mobile"]
TrackingStatus = Literal["new", "applied", "phone_screen", "interview", "offer", "rejected", "passed"]

@dataclass
class JobResult:
    title: str
    company: str
    location: str
    posted_date: str
    fit_score: int
    gaps: List[str]
    url: str
    track: str
    description: str = ""          # raw job description text
    score_rationale: str = ""      # LLM explanation of the score

@dataclass
class SkippedJob:
    title: str
    company: str
    url: str
    reason: str
    track: str

@dataclass
class TrackedJob:
    """A job the user has chosen to track through their application process."""
    url: str                          # unique key
    title: str
    company: str
    location: str
    fit_score: int
    track: str
    run_id: str
    added_at: str
    status: TrackingStatus = "new"
    notes: str = ""
    description: str = ""
    score_rationale: str = ""


@dataclass
class RunResult:
    run_id: str
    track: str
    triggered_by: TriggeredBy
    started_at: str
    completed_at: str
    jobs: List[JobResult] = field(default_factory=list)
    skipped: List[SkippedJob] = field(default_factory=list)
