"""Jira API interaction"""

from jira import JIRA, JIRAError
from typing import Optional
from autolog.models import WorklogEntry, ProcessingResult

class JiraClient:
    def __init__(self, base_url: str, email: str, api_key: str):
        self.base_url = base_url
        self.email = email
        self.api_key = api_key
        self.client: Optional[JIRA] = None

    def connect(self):
        self.client = JIRA(
            server=self.base_url,
            basic_auth=(self.email, self.api_key)
        )
        return self.client

    def create_worklog(self, entry: WorklogEntry) -> ProcessingResult:
        if not entry.issue_key:
            return ProcessingResult(False, entry, ValueError("Missing issue key"))

        try:
            issue = self.client.issue(entry.issue_key)
            worklog = self.client.add_worklog(
                issue=issue,
                timeSpentSeconds=entry.duration,
                started=entry.date,
                comment=entry.description
            )
            return ProcessingResult(True, entry)
        except JIRAError as e:
            return ProcessingResult(False, entry, e)
        except Exception as e:
            return ProcessingResult(False, entry, e)