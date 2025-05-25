from datetime import timedelta

from .base import ProviderBase


class OdooProvider(ProviderBase):
    default_start_time = "8:00"

    field_map = {
        "started": "Date",
        # Odoo’s “Quantity” is hours as float (e.g. 1.75)
        "duration": "Quantity",
        "description": "Description",
        "activity": "Task",
        "raw_issue_key": "Task",
    }

    def _post_process(self, mapped_data: dict[str, str]) -> dict[str, str]:
        start_date = mapped_data.get("started", "").strip()
        mapped_data["started"] = f"{start_date} {self.default_start_time}"

        # convert float hours → seconds
        try:
            duration = float(mapped_data.get("duration", "0"))
            td = timedelta(hours=duration)
            mapped_data["duration"] = td.seconds
        except ValueError:
            # leave it to the base parser to log/skip if unparsable
            pass

        return mapped_data
