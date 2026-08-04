import httpx


class HttpClient:
    """HTTP client wrapper for making requests."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def get(self, url: str, headers: dict | None = None) -> httpx.Response:
        """Make a GET request."""
        with httpx.Client(timeout=self.timeout) as client:
            return client.get(url, headers=headers)

    def post(
        self, url: str, data: dict | None = None, headers: dict | None = None
    ) -> httpx.Response:
        """Make a POST request."""
        with httpx.Client(timeout=self.timeout) as client:
            return client.post(url, json=data, headers=headers)
