"""Data models"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pytz


@dataclass
class WorklogEntry:
    started: datetime
    duration: int
    description: str
    activity: str
    timezone: Optional[str] = None
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

    def normalized_start_utc(self) -> datetime:
        """
        Return self.started as a UTC‐aware datetime.

        - If self.started is naïve, interpret it in self.timezone.
        - If self.started is already timezone‐aware, respect its tzinfo.
        """
        dt = self.started
        # If naïve, localize to self.timezone
        if dt.tzinfo is None:
            tz = pytz.timezone(self.timezone)
            dt = tz.localize(dt)
        # Convert any tz to UTC
        return dt.astimezone(pytz.UTC)

    def __eq__(self, other: "WorklogEntry"):
        self_start = self.normalized_start_utc()
        other_start = other.normalized_start_utc()
        time_match = (
            self_start.hour == other_start.hour
            and self_start.minute == other_start.minute
        )

        # Normalize comments
        def clean_text(text: str) -> str:
            return re.sub(r"\s+", " ", text.strip().lower())

        comment_match = clean_text(self.description) == clean_text(other.description)

        return time_match and comment_match


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
