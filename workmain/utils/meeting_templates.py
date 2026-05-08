"""
WorkmAIn Meeting Template Config
Meeting Templates v1.0
20260508

Manages recurring meeting templates stored in config/meeting_templates.json.
Templates define default parameters for recurring meeting creation patterns
(e.g. "Daily Standup", "Weekly Review").

Version History:
- v1.0: Initial implementation (Item 27)
"""

import json
from pathlib import Path
from typing import Dict, Optional


TEMPLATE_SCHEMA_KEYS = {"name", "start", "end", "frequency", "until_days", "include_weekends", "attendees"}
VALID_FREQUENCIES = {"daily", "weekly", "monthly"}


class MeetingTemplateConfig:
    """
    Manages recurring meeting templates backed by config/meeting_templates.json.

    Template schema:
        name (str): Template name (used as dict key)
        start (str): Wall-clock start time "HH:MM"
        end (str): Wall-clock end time "HH:MM"
        frequency (str): "daily" | "weekly" | "monthly"
        until_days (int): How many days ahead to create occurrences (default: 90)
        include_weekends (bool): Whether to create weekend occurrences (default: False)
        attendees (list[str]): Optional attendee email list
    """

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "meeting_templates.json"
        self.config_path = config_path
        self._templates: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self.config_path, "r") as f:
                self._templates = json.load(f)
        except FileNotFoundError:
            self._templates = {}

    def _save(self) -> None:
        with open(self.config_path, "w") as f:
            json.dump(self._templates, f, indent=2)
            f.write("\n")

    def get_all(self) -> Dict[str, dict]:
        """Return all templates keyed by name."""
        return dict(self._templates)

    def get(self, name: str) -> Optional[dict]:
        """Return a single template by name or None if not found."""
        return self._templates.get(name)

    def exists(self, name: str) -> bool:
        return name in self._templates

    def add(
        self,
        name: str,
        start: str,
        end: str,
        frequency: str,
        until_days: int = 90,
        include_weekends: bool = False,
        attendees: Optional[list] = None,
    ) -> None:
        """
        Add or overwrite a template.

        Args:
            name: Template name
            start: Start time "HH:MM"
            end: End time "HH:MM"
            frequency: "daily" | "weekly" | "monthly"
            until_days: Days ahead to create occurrences
            include_weekends: Create weekend occurrences for daily frequency
            attendees: Optional list of attendee emails
        """
        if frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")
        self._templates[name] = {
            "name": name,
            "start": start,
            "end": end,
            "frequency": frequency,
            "until_days": until_days,
            "include_weekends": include_weekends,
            "attendees": attendees or [],
        }
        self._save()

    def delete(self, name: str) -> bool:
        """
        Remove a template by name.

        Returns:
            True if removed, False if not found
        """
        if name not in self._templates:
            return False
        del self._templates[name]
        self._save()
        return True


_meeting_template_config_instance = None


def get_meeting_template_config() -> MeetingTemplateConfig:
    """Get singleton instance of MeetingTemplateConfig."""
    global _meeting_template_config_instance
    if _meeting_template_config_instance is None:
        _meeting_template_config_instance = MeetingTemplateConfig()
    return _meeting_template_config_instance
