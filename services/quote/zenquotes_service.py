"""ZenQuotes API integration for quote of the day functionality.

This module implements the QuoteService interface using the ZenQuotes API
(https://zenquotes.io). It provides production-ready quote fetching with
date-based caching to minimize API calls and handle network failures gracefully.

Key Features:
    - Daily quote caching (one API call per day maximum)
    - Automatic fallback quote on API failures
    - Error resilience with cached fallback to prevent repeated failed requests
    - HTTP client abstraction for testing and flexibility

API Integration:
    - Endpoint: https://zenquotes.io/api/today
    - Method: GET (no authentication required)
    - Rate Limit: Respect ZenQuotes API usage guidelines
    - Response Format: JSON array with single quote object
        [{"q": "quote text", "a": "author name", "h": "html"}]

Caching Strategy:
    The service caches quotes by date (using system local date):
    1. First call of the day fetches from API and caches
    2. Subsequent calls return cached quote (no API hit)
    3. Cache automatically invalidates at midnight
    4. Fallback quotes are also cached to prevent retry storms

Error Handling:
    All errors are caught and logged. The service returns a hardcoded fallback
    quote on any failure (network error, invalid response, etc.). The fallback
    is cached for the day to prevent repeated API calls when service is down.

Note:
    Uses system local date (not timezone-aware) for cache key. If the application
    needs timezone-specific caching, consider using DateTimeUtil.now().date()
    instead of date.today().
"""

import logging
from datetime import date

from services.quote.quote_service import Quote, QuoteService
from utils.http_client import HttpClient

logger = logging.getLogger(__name__)


class ZenQuotesService(QuoteService):
    """Production quote service implementation using ZenQuotes API.

    This class fetches inspirational quotes from the ZenQuotes API with
    intelligent caching to minimize network requests. It handles all error
    conditions gracefully and never raises exceptions to callers.

    The service maintains an internal cache indexed by date, ensuring at most
    one API call per calendar day. Both successful and fallback quotes are
    cached.

    Attributes:
        BASE_URL (str): Class constant for ZenQuotes API endpoint. The /api/today
            endpoint returns the "quote of the day" which changes daily.
        http_client (HttpClient): HTTP client instance for making requests.
            Injected for testability and flexibility.
        _cached_quote (Quote | None): Internal cache storing the most recent
            quote. None if no quote has been fetched yet.
        _cached_date (date | None): Date when _cached_quote was fetched.
            Used to invalidate cache at midnight.

    See Also:
        - QuoteService: Abstract base class defining the interface
        - HttpClient: HTTP client abstraction used for requests
        - display_clock.py: Integration point for e-paper display
    """

    BASE_URL = "https://zenquotes.io/api/today"

    def __init__(self, http_client: HttpClient | None = None):
        """Initialize ZenQuotes service with optional custom HTTP client.

        Args:
            http_client (HttpClient | None, optional): HTTP client instance to use
                for API requests. If None, creates a new HttpClient() instance.
                Providing a custom client is useful for testing or when sharing
                a configured client across multiple services. Defaults to None.
        """
        self.http_client = http_client or HttpClient()
        self._cached_quote: Quote | None = None
        self._cached_date: date | None = None

    def get_quote_of_the_day(self) -> Quote:
        """Fetch today's quote from ZenQuotes API with date-based caching.

        This method implements the QuoteService interface. It returns the quote
        of the day, using a cached value if available for today's date, or
        fetching a fresh quote from the ZenQuotes API if the cache is stale
        or empty.

        Caching Behavior:
            - First call: Fetches from API, caches result
            - Same day calls: Returns cached quote (no API request)
            - Next day: Cache miss triggers new API request
            - On error: Returns fallback quote and caches it

        Returns:
            Quote: The quote of the day with text and author fields populated.
                Never returns None. If the API fails, returns a hardcoded
                fallback quote (Steve Jobs quote about great work).

        API Response Format:
            The ZenQuotes API returns JSON array with one element:
                [
                    {
                        "q": "Quote text here",
                        "a": "Author Name",
                        "h": "<blockquote>...</blockquote>"
                    }
                ]

        Error Cases:
            All exceptions are caught and handled internally:
            - Network failures (connection timeout, DNS errors)
            - HTTP errors (404, 500, etc.)
            - Invalid JSON response
            - Empty response array
            - Missing fields in response

            In all error cases, logs the error and returns fallback quote.

        Note:
            Uses system local date (date.today()) not timezone-aware date.
            Cache invalidation happens at system midnight, not a specific timezone.
        """
        today = date.today()

        # Return cached quote if it's still today
        if self._cached_quote is not None and self._cached_date == today:
            logger.debug("Using cached quote for %s", today)
            return self._cached_quote

        # Fetch new quote
        logger.info("Fetching new quote for %s", today)
        try:
            response = self.http_client.get(self.BASE_URL)
            response.raise_for_status()

            data = response.json()
            if not data or len(data) == 0:
                raise Exception("Empty response from ZenQuotes API")  # noqa: TRY002

            quote_data = data[0]
            quote = Quote(text=quote_data["q"], author=quote_data["a"])

            # Cache the quote
            self._cached_quote = quote
            self._cached_date = today

            return quote

        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to fetch quote from ZenQuotes: {e}")
            # Return a fallback quote on error
            fallback = Quote(
                text="The only way to do great work is to love what you do.",
                author="Steve Jobs",
            )
            # Cache fallback to avoid repeated failed API calls
            self._cached_quote = fallback
            self._cached_date = today
            return fallback
