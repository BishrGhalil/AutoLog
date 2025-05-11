import logging
import time
from pathlib import Path
from typing import Callable, List, Tuple

import pytz
from jira.exceptions import JIRAError

from autolog.adapters import CSVAdapter
from autolog.constants import COOLDOWN_EVERY, COOLDOWN_SEC
from autolog.exceptions import DuplicateWorklogError
from autolog.issue_parser import IssueKeyParser
from autolog.jira_client import JiraClient
from autolog.models import ProcessingResult, WorklogEntry

logger = logging.getLogger(__file__)


class WorklogProcessor:
    """Handles business logic for processing worklog entries with Jira."""

    def __init__(self, credentials: Tuple[str, str, str], timezone: str):
        """Initialize the processor with Jira credentials and settings."""
        self.credentials = credentials
        self.client = None
        self.timezone = timezone
        self.results: List[ProcessingResult] = []
        self.failed_entries: List[ProcessingResult] = []
        self.total: int = 0

    def load_entries(self, file_path: Path) -> List[WorklogEntry]:
        """Load and preprocess worklog entries from a CSV file."""
        adapter = CSVAdapter()
        entries = adapter.parse(file_path)
        total_seconds = 0
        for idx, entry in enumerate(entries):
            entry.status = "pending"
            entry.issue_key = IssueKeyParser.parse(entry.raw_issue_key)
            entry._idx = idx
            entry.timezone = self.timezone
            tz = pytz.timezone(entry.timezone)
            entry.started = entry.started.astimezone(tz)
            total_seconds += entry.duration
        total_hours = f"{total_seconds // 3600}:{(total_seconds % 3600) // 60}"
        return entries, total_hours

    def process_entries(
        self,
        entries: List[WorklogEntry],
        callback: Callable[[int, int, WorklogEntry, ProcessingResult], None],
        prevent_duplicates: bool = True,
    ) -> None:
        """Process worklog entries in a background thread,
        invoking callback for UI updates.
        """
        try:
            self.results = []
            self.failed_entries = []
            self.client = JiraClient(
                *self.credentials, prevent_duplicates=prevent_duplicates
            )
            self.client.connect()
            entries_to_process = [
                e for e in entries if e.status in ("pending", "failed", "skipped")
            ]
            total = len(entries_to_process)
            self.total = total
            unique_issues = {e.issue_key for e in entries_to_process if e.issue_key}

            if self.client.prevent_duplicates:
                self.client.preload_worklogs(list(unique_issues))

            for idx, entry in enumerate(entries_to_process, 1):
                result = self._process_single_entry(entry)
                callback(idx, total, entry, result)
                if idx % COOLDOWN_EVERY == 0 and idx != len(entries_to_process):
                    time.sleep(COOLDOWN_SEC)

        except JIRAError as e:
            logger.error(f"Jira error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise

    def _process_single_entry(self, entry: WorklogEntry) -> ProcessingResult:
        """Process a single worklog entry and update its status."""
        result = self.client.create_worklog(entry)
        if result.success:
            entry.status = "success"
        elif isinstance(result.error, DuplicateWorklogError):
            entry.status = "skipped"
        else:
            entry.status = "failed"
        self.results.append(result)
        if not result.success:
            self.failed_entries.append(result)
        return result
