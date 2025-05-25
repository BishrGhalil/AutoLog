from .base import ProviderBase


class KimaiProvider(ProviderBase):
    field_map = {
        "started": ["Date", "From"],
        "duration": "Duration",
        "description": "Description",  # optional
        "activity": "Activity",
        "raw_issue_key": "Activity",  # override if needed
    }
