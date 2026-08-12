"""Datetime utilities with timezone support."""

from datetime import UTC, datetime, timedelta, timezone


class DateTimeUtil:
    """Utility class for timezone-aware datetime operations."""

    # Indian Standard Time (IST) - UTC+5:30
    IST = timezone(timedelta(hours=5, minutes=30))

    @staticmethod
    def now() -> datetime:
        """Get current datetime in IST timezone.

        Returns:
            datetime: Current datetime with IST timezone
        """
        return datetime.now(tz=DateTimeUtil.IST)

    @staticmethod
    def now_utc() -> datetime:
        """Get current datetime in UTC timezone.

        Returns:
            datetime: Current datetime with UTC timezone
        """
        return datetime.now(tz=UTC)

    @staticmethod
    def to_ist(dt: datetime) -> datetime:
        """Convert datetime to IST timezone.

        Args:
            dt: Datetime to convert

        Returns:
            datetime: Datetime converted to IST timezone
        """
        return dt.astimezone(DateTimeUtil.IST)
