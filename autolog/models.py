"""Data models"""

from dataclasses import dataclass
from datetime import datetime

@dataclass
class WorklogEntry:
    date: datetime
    duration: int
    description: str
    activity: str
    raw_issue_key: str = None
    issue_key: str = None
    status: str = "pending"

@dataclass
class ProcessingResult:
    success: bool
    entry: WorklogEntry
    error: Exception = None