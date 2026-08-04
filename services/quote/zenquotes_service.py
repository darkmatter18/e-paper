import logging
from datetime import date

from services.quote.quote_service import Quote, QuoteService
from utils.http_client import HttpClient

logger = logging.getLogger(__name__)


class ZenQuotesService(QuoteService):
    """ZenQuotes API implementation of QuoteService with daily caching."""

    BASE_URL = "https://zenquotes.io/api/today"

    def __init__(self, http_client: HttpClient | None = None):
        self.http_client = http_client or HttpClient()
        self._cached_quote: Quote | None = None
        self._cached_date: date | None = None

    def get_quote_of_the_day(self) -> Quote:
        """Fetch today's quote from ZenQuotes API with daily caching.

        Returns:
            Quote: The quote of the day (cached if already fetched today)

        Raises:
            Exception: If the API request fails
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
