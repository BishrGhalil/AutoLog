"""Data input adapters"""

from abc import ABC, abstractmethod
import csv
from datetime import datetime
from pathlib import Path
from autolog.models import WorklogEntry
from autolog.issue_parser import IssueKeyParser

class DataAdapter(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> list[WorklogEntry]:
        pass

class CSVAdapter(DataAdapter):
    def parse(self, file_path: Path) -> list[WorklogEntry]:
        entries = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = datetime.strptime(row['Date'], '%Y-%m-%d')
                entries.append(WorklogEntry(
                    date=date,
                    duration=int(row['Duration']),
                    description=row.get('Description', ""),
                    activity=row['Activity'],
                    raw_issue_key=IssueKeyParser.parse(row['Activity'])
                ))
        return entries