"""GiveRadar Python client.

    from giveradar import Client
    gr = Client()                      # reads GIVERADAR_API_KEY
    for c in gr.search("oxfam", country="GB")["results"]:
        print(c["name"], c["trust_score"])

Get a free key at https://giveradar.com/api/keys/ (10 requests/day; Pro 10,000/day).
"""
from .client import Client
from .errors import (APIError, AuthenticationError, GiveRadarError, NotFoundError,
                     RateLimitError)

__version__ = "0.1.0"
__all__ = ["Client", "GiveRadarError", "AuthenticationError", "RateLimitError",
           "NotFoundError", "APIError", "__version__"]
