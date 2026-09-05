class GiveRadarError(Exception):
    """Base class for all client errors."""


class AuthenticationError(GiveRadarError):
    """No API key, or the key was rejected (HTTP 401/403)."""


class RateLimitError(GiveRadarError):
    """Daily quota exhausted (HTTP 429). Free keys allow 10 requests/day."""


class NotFoundError(GiveRadarError):
    """No charity with that slug (HTTP 404)."""


class APIError(GiveRadarError):
    """Any other non-2xx response."""

    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
