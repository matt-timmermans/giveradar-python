# Changelog

## Unreleased

API changes on giveradar.com (2026-10-21). No client code change is needed: `charity()` returns the API's JSON as before.

- `officers`: one entry per person per fiscal year, with a new `former` flag (former officer, director or trustee in that filing).
- New Pro fields: `officers_total` (number of people, not rows) and `sources` (where each part of the record comes from: section, name, url, as_of, note).
- `top_exec_name`, `top_exec_title` and `top_exec_compensation` always describe the same person.
- Removed fields: `charity_navigator_rating`, `charity_navigator_score`, `cn_financial_score`, `cn_accountability_score`, `cn_advisories`, `guidestar_seal` and `sanctions_status`.
- `data_sources` is deprecated: it now lists only public source keys and will be removed in a later release. Use `sources`.

## 0.1.0 (2026-09-05)

- First release: client for search, charity, financials, news, stats, reviews; CLI with search, verify, charity, financials, news, stats.
