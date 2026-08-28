from dataclasses import dataclass, field
from typing import List, Literal

TriggeredBy = Literal["ui", "schedule", "claude-mobile"]

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

@dataclass
class RunResult:
    run_id: str
    track: str
    triggered_by: TriggeredBy
    started_at: str
    completed_at: str
    jobs: List[JobResult] = field(default_factory=list)
