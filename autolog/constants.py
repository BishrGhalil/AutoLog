from enum import Enum
from typing import Dict

COOLDOWN_SEC: float = 2.0
COOLDOWN_EVERY: int = 10

TABLE_COLUMN_WIDTHS: Dict[str, int] = {
    "Started": 160,
    "Duration": 100,
    "Issue": 150,
    "Status": 80,
    "Error": 400,
}


class ColumnID(Enum):
    STARTED = "#1"
    DURATION = "#2"
    ISSUE = "#3"
    STATUS = "#4"
    ERROR = "#5"


STATUS_DISPLAY = {
    "pending": "🔄 Pending",
    "success": "✅ Success",
    "failed": "❌ Failed",
    "skipped": "⏭️ Skipped",
}
