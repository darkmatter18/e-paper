"""Timezone-aware datetime utilities for the e-paper clock application.

This module provides a centralized utility class for handling datetime operations
with timezone awareness. The primary focus is on Indian Standard Time (IST) which
is used throughout the e-paper clock application for display and scheduling.

Key Components:
    - DateTimeUtil: Static utility class for timezone operations
    - IST timezone constant: UTC+5:30 offset for Indian Standard Time

Timezone Handling:
    All datetime objects returned by this module are timezone-aware. The module
    ensures consistent timezone handling across the application, preventing
    naive datetime issues.

Note:
    This module uses the built-in datetime.timezone class rather than pytz
    for simplicity, as IST has no daylight saving time transitions.
"""

from datetime import UTC, datetime, timedelta, timezone


class DateTimeUtil:
    """Static utility class for timezone-aware datetime operations.

    This class provides methods for working with timezone-aware datetime objects,
    with a focus on Indian Standard Time (IST). All methods are static and do not
    require instantiation.

    Attributes:
        IST (timezone): Indian Standard Time timezone object (UTC+5:30).
            This is a class-level constant used throughout the application.
    """

    # Indian Standard Time (IST) - UTC+5:30
    # No daylight saving time, so a simple fixed offset is sufficient
    IST = timezone(timedelta(hours=5, minutes=30))

    @staticmethod
    def now() -> datetime:
        """Get current datetime in IST timezone.

        Returns the current system time converted to Indian Standard Time.
        The returned datetime object is timezone-aware.

        Returns:
            datetime: Current datetime with IST timezone info attached.
                The datetime is fully timezone-aware and can be safely
                compared with other timezone-aware datetime objects.
        """
        return datetime.now(tz=DateTimeUtil.IST)

    @staticmethod
    def now_utc() -> datetime:
        """Get current datetime in UTC timezone.

        Returns the current system time in Coordinated Universal Time (UTC).
        The returned datetime object is timezone-aware.

        Returns:
            datetime: Current datetime with UTC timezone info attached.
                Useful for logging, API calls, or when UTC timestamps
                are required.
        """
        return datetime.now(tz=UTC)

    @staticmethod
    def to_ist(dt: datetime) -> datetime:
        """Convert any datetime to IST timezone.

        Converts a timezone-aware datetime to Indian Standard Time. If the input
        datetime is naive (no timezone info), it will be treated as UTC and then
        converted to IST.

        Args:
            dt (datetime): Datetime object to convert. Should be timezone-aware
                for accurate conversion. If naive, assumes UTC.

        Returns:
            datetime: The input datetime converted to IST timezone. The returned
                datetime preserves the same instant in time, just expressed in
                a different timezone.

        Note:
            If the input datetime is naive (no tzinfo), the behavior follows
            Python's datetime.astimezone() semantics, which assumes local time
            on Python 3.6+ or raises an exception on earlier versions.
        """
        return dt.astimezone(DateTimeUtil.IST)
