"""
Plain module-level time and duration parsing — extracted from
TimeEntriesRepository, where these functions lived despite having no
session or repository-state dependency. Matches the location CLAUDE.md
and the project custom instructions have described since early in the
project.
"""

from datetime import datetime, time


def parse_duration_hours(duration_str: str) -> float:
    """
    Parse duration string to hours.

    Args:
        duration_str: Duration string (e.g., "1.5h", "2h", "30m", "1h30m")

    Returns:
        Duration in hours as float

    Raises:
        ValueError: If duration string is invalid
    """
    duration_str = duration_str.lower().strip()

    # Handle formats: 1.5h, 2h, 30m, 1h30m
    hours = 0.0
    minutes = 0.0

    # Check for hours
    if 'h' in duration_str:
        parts = duration_str.split('h')
        try:
            hours = float(parts[0])
            # Check if there are minutes after hours
            if len(parts) > 1 and parts[1]:
                remainder = parts[1].replace('m', '').strip()
                if remainder:
                    minutes = float(remainder)
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")

    # Check for minutes only
    elif 'm' in duration_str:
        try:
            minutes = float(duration_str.replace('m', '').strip())
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")

    # Try parsing as plain number (assume hours)
    else:
        try:
            hours = float(duration_str)
        except ValueError:
            raise ValueError(
                f"Invalid duration format: {duration_str}. "
                "Expected format: 1.5h, 2h, 30m, or 1h30m"
            )

    # Convert to total hours
    total_hours = hours + (minutes / 60.0)

    return total_hours


def parse_time(time_str: str) -> time:
    """
    Parse time string to time object (24-hour format).

    Supports multiple formats:
    - 24-hour with colon: "14:30", "09:00"
    - 24-hour without colon: "1430", "0900", "930"
    - 12-hour with colon: "2:30pm", "9:00am"
    - 12-hour without colon: "230pm", "900am"

    Args:
        time_str: Time string

    Returns:
        time object in 24-hour format

    Raises:
        ValueError: If time string is invalid
    """
    time_str = time_str.lower().strip()

    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    time_str = time_str.replace('am', '').replace('pm', '').strip()

    if ':' in time_str:
        try:
            parsed = datetime.strptime(time_str, '%H:%M').time()
            if is_pm and parsed.hour != 12:
                parsed = parsed.replace(hour=parsed.hour + 12)
            elif is_am and parsed.hour == 12:
                parsed = parsed.replace(hour=0)
            return parsed
        except ValueError:
            pass

    try:
        if len(time_str) == 3:
            time_str = '0' + time_str
        elif len(time_str) == 1 or len(time_str) == 2:
            time_str = time_str.zfill(2) + '00'

        if len(time_str) == 4:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            if hours > 23 or minutes > 59:
                raise ValueError("Invalid hours or minutes")
            if is_pm and hours != 12:
                hours += 12
            elif is_am and hours == 12:
                hours = 0
            return time(hours, minutes)
    except (ValueError, IndexError):
        pass

    raise ValueError(
        f"Invalid time format: {time_str}. "
        "Expected format: HH:MM (24hr) or H:MMam/pm (12hr)"
    )
