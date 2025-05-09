"""Data models"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class WorklogEntry:
    started: datetime
    duration: int
    description: str
    activity: str
    raw_issue_key: str = None
    issue_key: str = None
    status: str = "pending"

    _idx: int = 0

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"{self.raw_issue_key},"
            f"{self.started},"
            f"{self.status}"
            ")"
        )


@dataclass
class ProcessingResult:
    success: bool
    entry: WorklogEntry
    error: Exception = None

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"{self.success},"
            f"{self.error},"
            f"{self.entry}"
            ")"
        )
