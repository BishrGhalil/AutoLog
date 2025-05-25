# autolog/update_checker.py

import requests
from packaging import version


def get_latest_release_info(repo: str) -> dict:
    """
    Fetches the latest GitHub release for `repo` (e.g. "username/repo").
    Returns a dict with:
      - version: tag name (string)
      - changelog: body of the release (string)
      - url: HTML URL of the release page (string)
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return {
        "version": data["tag_name"],
        "changelog": data.get("body", "").strip(),
        "url": data["html_url"],
    }


def is_update_available(current: str, latest: str) -> bool:
    return version.parse(latest) > version.parse(current)
