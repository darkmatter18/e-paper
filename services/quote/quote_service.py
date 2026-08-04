from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Quote:
    """Quote data model."""

    text: str
    author: str


class QuoteService(ABC):
    """Abstract base class for quote services."""

    @abstractmethod
    def get_quote_of_the_day(self) -> Quote:
        """Fetch the quote of the day."""
