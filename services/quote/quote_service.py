"""Abstract base classes and data models for quote services.

This module defines the contract for quote service implementations used in the
e-paper clock application. It provides a simple abstraction layer that allows
different quote providers (ZenQuotes, custom APIs, local databases) to be used
interchangeably.

Key Components:
    - Quote: Immutable data class representing a quote with text and author
    - QuoteService: Abstract base class defining the quote service interface

Architecture Notes:
    The abstract base class pattern allows the display code to depend on the
    interface rather than specific implementations. This makes it easy to:
    - Switch between quote providers
    - Add caching strategies per implementation
    - Mock services for testing
    - Support offline/fallback modes

Service implementations should handle:
    - API authentication and rate limiting
    - Caching to reduce API calls
    - Error handling with fallback quotes
    - Network timeouts and retries
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Quote:
    """Immutable data model representing a quotation.

    A quote consists of the text content and attribution to an author. This
    class uses @dataclass for automatic generation of __init__, __repr__,
    __eq__, and other methods.

    Attributes:
        text (str): The main content of the quote. Should be the complete
            quote text without surrounding punctuation (quotes are added
            during display).
        author (str): Attribution for the quote. Typically a person's name,
            but may be "Unknown", "Anonymous", or other descriptive text.

    Note:
        This is a simple data container with no business logic. All quote
        processing (formatting, wrapping, display) is handled by the rendering
        layer in display_clock.py.
    """

    text: str
    author: str


class QuoteService(ABC):
    """Abstract base class defining the contract for quote service implementations.

    This abstract class establishes the interface that all quote services must
    implement. Subclasses should handle API communication, caching, error handling,
    and any provider-specific logic.

    The interface is intentionally minimal to support different quote sources:
    - Web APIs (ZenQuotes, Quotable, custom services)
    - Local databases or JSON files
    - Static quote collections
    - Mock implementations for testing

    Implementing Classes:
        Implementations should provide:
        - API/data source integration
        - Caching strategy (by date, time, or other criteria)
        - Error handling with fallback quotes
        - Rate limiting and retry logic
        - Logging for debugging

    See Also:
        - ZenQuotesService: Production implementation using ZenQuotes API
        - display_clock.py: Integration into the e-paper display system
    """

    @abstractmethod
    def get_quote_of_the_day(self) -> Quote:
        """Fetch the quote of the day from the service.

        This method should return a quote appropriate for the current day.
        Implementations are free to define "day" in their own context
        (local time, UTC, or based on API semantics).

        The method should handle all error cases internally and either return
        a valid Quote object or a fallback quote. It should never raise
        exceptions to the caller.

        Returns:
            Quote: A Quote object with text and author populated. Should never
                return None. If the service fails, implementations should return
                a hardcoded fallback quote.

        Raises:
            NotImplementedError: If called on the abstract base class directly.

        Implementation Guidelines:
            - Cache results to avoid repeated API calls (daily caching recommended)
            - Handle network errors gracefully with fallback quotes
            - Log errors for debugging but don't propagate exceptions
            - Respect API rate limits and usage terms
            - Return consistent results throughout the same day
        """
