"""Data input adapters"""

import csv
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from dateutil import parser

from autolog.models import WorklogEntry

logger = logging.getLogger(__file__)


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
                try:
                    started = parser.parse(datetime_str)
                except Exception as e:
                    logger.exception(e)
                    continue
                else:
                    entries.append(
                        WorklogEntry(
                            started=started,
                            duration=int(row["Duration"]),
                            description=row.get("Description", ""),
                            activity=row["Activity"],
                            raw_issue_key=row["Activity"],
                        )
                    )
        return entries
