from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Detection:
    common_name: str
    scientific_name: str
    confidence: float
    start_s: float
    end_s: float


@dataclass
class JournalEntry:
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    place: str | None = None
    detections: list[Detection] = field(default_factory=list)
