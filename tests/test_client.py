import os
import pytest
import responses

from giveradar import Client, AuthenticationError, RateLimitError, NotFoundError

BASE = "https://giveradar.com/api/v1"


def test_requires_key(monkeypatch):
    monkeypatch.delenv("GIVERADAR_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        Client().stats()


@responses.activate
def test_search_sends_bearer_and_params():
    responses.get(f"{BASE}/search/", json={"query": "oxfam", "country": "GB", "count": 1,
                                          "results": [{"slug": "oxfam", "name": "Oxfam", "country_code": "GB", "trust_score": 88}]})
    out = Client(api_key="gr_test").search("oxfam", country="GB")
    assert out["count"] == 1 and out["results"][0]["slug"] == "oxfam"
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer gr_test"
    assert "q=oxfam" in req.url and "country=GB" in req.url


@responses.activate
def test_errors_map_to_exceptions():
    responses.get(f"{BASE}/charity/nope/", status=404)
    responses.get(f"{BASE}/stats/", status=429)
    responses.get(f"{BASE}/charity/x/news/", status=401)
    c = Client(api_key="gr_test")
    with pytest.raises(NotFoundError):
        c.charity("nope")
    with pytest.raises(RateLimitError):
        c.stats()
    with pytest.raises(AuthenticationError):
        c.news("x")


@responses.activate
def test_submit_review_posts_json():
    responses.post(f"{BASE}/charity/oxfam/reviews/", json={"ok": True}, status=201)
    Client(api_key="gr_test").submit_review("oxfam", "Jane", 5, "Great", comment="Clear reporting")
    body = responses.calls[0].request.body
    assert b'"rating": 5' in body and b'"user_role": "donor"' in body


@pytest.mark.skipif(not os.environ.get("GIVERADAR_API_KEY"), reason="live smoke test needs GIVERADAR_API_KEY")
def test_live_stats():
    out = Client().stats()
    assert out["total_charities"] > 1_000_000
