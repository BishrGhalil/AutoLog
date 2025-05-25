import logging
from abc import ABC
from pathlib import Path

from dateutil import parser as date_parser

from autolog.models import WorklogEntry
from autolog.parsers.file_parsers import select_file_parser

logger = logging.getLogger(__file__)


class ParserError(Exception):
    pass


class ProviderBase(ABC):
    # provider must define a field_map: WorklogEntry attr → column name(s)
    field_map: dict[str, str | list[str]]
    _required_fields = ["started", "duration", "activity"]

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.parser = select_file_parser(file_path)

    def parse(self) -> list[WorklogEntry]:
        raw_rows = self.parser.read(self.file_path)
        entries = []
        for row in raw_rows:
            data = self._map_fields(row)
            data = self._post_process(data)
            try:
                # parse date/time if needed
                data["started"] = date_parser.parse(data["started"])
                data["duration"] = int(data["duration"])
            except Exception as e:
                logger.exception(f"Skipping row due to parse error: {e}")
                continue
            entries.append(WorklogEntry(**data))
        return entries

    def _map_fields(self, row: dict) -> dict:
        mapped = {}
        for attr, cols in self.field_map.items():
            plural = False
            if isinstance(cols, (list, tuple)):
                plural = True
                # join multiple cols with space by default
                values = [row.get(col, "") for col in cols]
                value = " ".join(values).strip()
            else:
                value = row.get(cols, "").strip()

            if not value and attr in self._required_fields:
                raise ParserError(
                    "Invalid file: missing required "
                    f"`{cols}` column{'s' if plural else ''} "
                    "for this provider."
                )
            mapped[attr] = value
        return mapped

    def _post_process(self, mapped_data: dict[str, str]) -> dict[str, str]:
        """
        Hook for providers to:
         - convert units (e.g. hours→seconds)
         - rename/override fields
        """
        return mapped_data
