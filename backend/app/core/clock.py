"""Time helpers.

Timestamp columns are timezone-naive and always hold UTC, so application code uses ``utcnow()``
rather than ``datetime.now()`` (local time) or the deprecated ``datetime.utcnow()``.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime, matching how timestamps are stored."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
