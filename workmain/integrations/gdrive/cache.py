"""
WorkmAIn Google Drive Cache
gdrive/cache.py v1.0
20260309

Folder ID cache for Google Drive integration.
Avoids re-querying Drive on every command by persisting folder IDs locally.

Cache file: ~/.workmain/integrations/gdrive/cache.json  (chmod 600)

Cache structure:
    {
        "YYYYMM": {
            "root":      "<folder_id>",
            "Raw_Notes": "<folder_id>",
            "Reports":   "<folder_id>",
            "Clockify":  "<folder_id>"
        }
    }

Version History:
- v1.0: Initial implementation (Phase 7 Gate 2)
"""

import json
from pathlib import Path
from typing import Optional


CACHE_PATH = Path.home() / ".workmain" / "integrations" / "gdrive" / "cache.json"


def load_cache() -> dict:
    """
    Load the folder ID cache from disk.

    Returns:
        Cache dict, or empty dict if the file does not exist or is malformed.
    """
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache: dict) -> None:
    """
    Persist the folder ID cache to disk (chmod 600).

    Args:
        cache: Cache dict to write.
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))
    CACHE_PATH.chmod(0o600)


def get_folder_id(period: str, subfolder: Optional[str] = None) -> Optional[str]:
    """
    Return a cached folder ID.

    Args:
        period: Month key in YYYYMM format (e.g. '202603').
        subfolder: One of 'root', 'Raw_Notes', 'Reports', 'Clockify'.
                   Pass None to look up the period root folder.

    Returns:
        Folder ID string, or None if not cached.
    """
    cache = load_cache()
    period_entry = cache.get(period, {})
    key = subfolder if subfolder is not None else "root"
    return period_entry.get(key)


def set_folder_id(period: str, subfolder: Optional[str], folder_id: str) -> None:
    """
    Store a folder ID in the cache and persist to disk.

    Args:
        period: Month key in YYYYMM format (e.g. '202603').
        subfolder: One of 'root', 'Raw_Notes', 'Reports', 'Clockify'.
                   Pass None to store the period root folder.
        folder_id: Google Drive folder ID to cache.
    """
    cache = load_cache()
    if period not in cache:
        cache[period] = {}
    key = subfolder if subfolder is not None else "root"
    cache[period][key] = folder_id
    save_cache(cache)
