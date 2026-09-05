from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from .errors import APIError, AuthenticationError, NotFoundError, RateLimitError

DEFAULT_BASE_URL = "https://giveradar.com/api/v1"
ENV_KEY = "GIVERADAR_API_KEY"


class Client:
    """Thin client for the GiveRadar REST API (https://giveradar.com/api/docs/).

    The key is read from the ``api_key`` argument or the ``GIVERADAR_API_KEY``
    environment variable and sent as ``Authorization: Bearer``. Every method
    returns the decoded JSON body as a dict, exactly as the API sends it.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = DEFAULT_BASE_URL,
                 timeout: float = 20.0, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.environ.get(ENV_KEY) or ""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        from . import __version__
        self._session.headers.update({
            "Accept": "application/json",
            "User-Agent": f"giveradar-python/{__version__} (+https://github.com/matt-timmermans/giveradar-python)",
        })

    # ---- HTTP -------------------------------------------------------------
    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                 json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise AuthenticationError(
                "No API key. Pass api_key=... or set GIVERADAR_API_KEY. "
                "Free keys (10 requests/day): https://giveradar.com/api/keys/")
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = self._session.request(method, url, params={k: v for k, v in (params or {}).items() if v is not None},
                                         json=json, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise APIError(0, f"network error: {e.__class__.__name__}: {e}") from e
        def _detail():
            try:
                d = resp.json()
                return str(d.get("detail") or d.get("error") or "").strip()
            except ValueError:
                return ""
        if resp.status_code in (401, 403):
            msg = _detail()
            if "limit" in msg.lower() or "quota" in msg.lower():
                raise RateLimitError(msg + " Pro keys allow 10,000/day: https://giveradar.com/api/")
            raise AuthenticationError((msg + " " if msg else "") + f"(HTTP {resp.status_code}). Get a key at https://giveradar.com/api/keys/")
        if resp.status_code == 429:
            raise RateLimitError((_detail() or "Daily request limit reached. Free keys allow 10/day") + "; Pro allows 10,000/day: https://giveradar.com/api/")
        if resp.status_code == 404:
            raise NotFoundError(f"Not found: {path}")
        if resp.status_code >= 400:
            try:
                msg = resp.json().get("error") or resp.json().get("detail") or resp.text[:200]
            except ValueError:
                msg = resp.text[:200]
            raise APIError(resp.status_code, str(msg))
        try:
            return resp.json()
        except ValueError:
            raise APIError(resp.status_code, "response was not JSON")

    # ---- Endpoints --------------------------------------------------------
    def search(self, query: str, country: Optional[str] = None) -> Dict[str, Any]:
        """Search charities by name or EIN. ``country`` is a 2-letter ISO code.
        Returns {"query", "country", "count", "results": [CharitySummary...]}."""
        return self._request("GET", "/search/", params={"q": query, "country": country})

    def charity(self, slug: str) -> Dict[str, Any]:
        """Full charity profile: registration, financials, officers, red flags, review summary."""
        return self._request("GET", f"/charity/{slug}/")

    def financials(self, slug: str) -> Dict[str, Any]:
        """Up to 10 years of filings plus spending breakdown and executive compensation (Pro)."""
        return self._request("GET", f"/charity/{slug}/financials/")

    def news(self, slug: str) -> Dict[str, Any]:
        """Recent news articles and average tone for a charity."""
        return self._request("GET", f"/charity/{slug}/news/")

    def stats(self) -> Dict[str, Any]:
        """Platform-wide totals: charities, countries, red flags, average integrity score."""
        return self._request("GET", "/stats/")

    def submit_review(self, slug: str, user_name: str, rating: int, title: str,
                      comment: str = "", user_role: str = "donor") -> Dict[str, Any]:
        """Submit a 1-5 star review for a charity (goes through GiveRadar's verification)."""
        body = {"user_name": user_name, "rating": int(rating), "title": title,
                "comment": comment, "user_role": user_role}
        return self._request("POST", f"/charity/{slug}/reviews/", json=body)

    # ---- Registry lookup (via the MCP server) ------------------------------
    MCP_URL = "https://giveradar.com/mcp/"

    def verify(self, id_value: str, country: str) -> Dict[str, Any]:
        """Look a charity up by registration number, charity number or EIN in a
        given country (ISO 3166-1 alpha-2). Uses the GiveRadar MCP server's
        ``verify_charity`` tool, which matches on the official identifier fields
        (the REST search matches names and EINs only). Works without a key at the
        anonymous rate (10/day per IP); a key raises the limit.

        Returns ``{"matches": [...], "count": n}`` or ``{"match": None, ...}``."""
        import json as _json
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "verify_charity",
                              "arguments": {"country": country.strip().upper(), "id_value": id_value.strip()}}}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = self._session.post(self.MCP_URL, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise APIError(0, f"network error: {e.__class__.__name__}: {e}") from e
        if resp.status_code == 429:
            raise RateLimitError("MCP quota reached (10/day anonymous). Pass an API key to raise it.")
        if resp.status_code >= 400:
            raise APIError(resp.status_code, resp.text[:200])
        data = resp.json()
        if "error" in data:
            raise APIError(400, str(data["error"].get("message", data["error"])))
        result = data.get("result") or {}
        if result.get("structuredContent"):
            return result["structuredContent"]
        for part in result.get("content") or []:
            if part.get("type") == "text":
                try:
                    return _json.loads(part["text"])
                except ValueError:
                    return {"text": part["text"]}
        return result
