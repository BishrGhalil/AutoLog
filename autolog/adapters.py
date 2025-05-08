"""Data input adapters"""

import csv
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from autolog.issue_parser import IssueKeyParser
from autolog.models import WorklogEntry


class DataAdapter(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> list[WorklogEntry]:
        pass


class CSVAdapter(DataAdapter):
    def parse(self, file_path: Path) -> list[WorklogEntry]:
        entries = []
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                datetime_str = f"{row['Date']} {row['From']}"
                started = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                entries.append(
                    WorklogEntry(
                        started=started,
                        duration=int(row["Duration"]),
                        description=row.get("Description", ""),
                        activity=row["Activity"],
                        raw_issue_key=IssueKeyParser.parse(row["Activity"]),
                    )
                )
        return entries
