"""Jira API interaction"""

from datetime import datetime

import pytz
from jira import JIRA, JIRAError

from autolog.exceptions import DuplicateWorklogError
from autolog.models import ProcessingResult, WorklogEntry

JIRA_TIMEOUT = 60


class JiraClient:
    def __init__(
        self, base_url: str, email: str, api_key: str, prevent_duplicates: bool = True
    ):
        self.base_url = base_url
        self.email = email
        self.api_key = api_key
        self.client: JIRA | None = None
        self.prevent_duplicates = prevent_duplicates
        self.worklog_cache = {}

    def connect(self):
        self.client = JIRA(
            server=self.base_url,
            basic_auth=(self.email, self.api_key),
            timeout=JIRA_TIMEOUT,
            async_=True,
        )
        return self.client

    def _convert_jira_worklog(self, worklog) -> WorklogEntry:
        """Convert JIRA worklog to our model with UTC timezone"""
        started = datetime.strptime(worklog.started, "%Y-%m-%dT%H:%M:%S.%f%z")
        return WorklogEntry(
            activity=worklog.issueId,
            started=started,
            duration=worklog.timeSpentSeconds,
            description=worklog.comment if hasattr(worklog, "comment") else "",
            raw_issue_key="",
            issue_key=worklog.issueId,
            timezone="UTC",  # Jira times are always UTC
        )

    def preload_worklogs(self, issue_keys: list[str]) -> None:
        """Prefetch worklogs only if duplicate prevention is enabled"""
        if not self.prevent_duplicates:
            return

        for key in issue_keys:
            if key not in self.worklog_cache:
                try:
                    self.worklog_cache[key] = self.client.worklogs(key)
                except JIRAError:
                    self.worklog_cache[key] = []

    def create_worklog(self, entry: WorklogEntry) -> ProcessingResult:
        if not entry.issue_key:
            return ProcessingResult(False, entry, ValueError("Missing issue key"))

        try:
            if self.prevent_duplicates:
                cached = self.worklog_cache.get(entry.issue_key, [])
                for jira_worklog in cached:
                    cached_entry = self._convert_jira_worklog(jira_worklog)
                    if entry == cached_entry:
                        return ProcessingResult(
                            False,
                            entry,
                            DuplicateWorklogError("Duplicate worklog entry detected"),
                        )

            new_worklog = self.client.add_worklog(
                issue=entry.issue_key,
                timeSpentSeconds=entry.duration,
                started=(
                    entry.started.astimezone(pytz.UTC)
                    if entry.started.tzinfo
                    else entry.started
                ),
                comment=entry.description,
            )

            if self.prevent_duplicates:
                if entry.issue_key in self.worklog_cache:
                    self.worklog_cache[entry.issue_key].append(new_worklog)
                else:
                    self.worklog_cache[entry.issue_key] = [new_worklog]

            return ProcessingResult(True, entry)
        except JIRAError as e:
            return ProcessingResult(False, entry, e)
