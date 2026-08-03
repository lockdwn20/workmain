"""
Shared utility for parsing human-readable duration strings into timedelta objects.
Used by meetings upcoming and other commands that accept time-window arguments.

Supported formats:
  Nd  — N days   (e.g., 7d, 14d)
  Nw  — N weeks  (e.g., 2w)
  Nm  — N months (e.g., 1m, approximated as N * 30 days)
"""

from datetime import timedelta


def parse_duration(value: str) -> timedelta:
    """
    Parse a human-readable duration string into a timedelta.

    Args:
        value: Duration string (e.g., '7d', '2w', '1m')

    Returns:
        timedelta representing the duration

    Raises:
        ValueError: If the format is invalid or unit is missing
    """
    value = value.strip()

    if not value:
        raise ValueError("Duration cannot be empty. Use e.g., 7d (days), 2w (weeks), 1m (month)")

    if value.isdigit():
        raise ValueError(
            f"Please specify a unit: e.g., {value}d (days), {value}w (weeks), {value}m (months)"
        )

    unit = value[-1].lower()
    number_part = value[:-1]

    if not number_part.isdigit():
        raise ValueError(
            f"Invalid duration format: '{value}'. Use Nd (days), Nw (weeks), or Nm (months)"
        )

    n = int(number_part)

    if n <= 0:
        raise ValueError(f"Duration must be a positive number, got: {n}")

    if unit == 'd':
        return timedelta(days=n)
    elif unit == 'w':
        return timedelta(weeks=n)
    elif unit == 'm':
        return timedelta(days=n * 30)
    else:
        raise ValueError(
            f"Unknown unit '{unit}' in '{value}'. Use d (days), w (weeks), or m (months)"
        )


__all__ = ['parse_duration']
