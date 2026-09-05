"""giveradar CLI.

    giveradar search "oxfam" --country GB
    giveradar charity against-malaria-foundation
    giveradar verify 1105319 --country GB
    giveradar financials against-malaria-foundation
    giveradar news against-malaria-foundation
    giveradar stats
Add --json to any command for raw output. Key: --key or GIVERADAR_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .client import Client
from .errors import GiveRadarError


def _money(v):
    if v is None:
        return "-"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if v >= 1e9:
        return f"{v/1e9:.1f}B"
    if v >= 1e6:
        return f"{v/1e6:.1f}M"
    if v >= 1e3:
        return f"{v/1e3:.0f}K"
    return f"{v:.0f}"


def _print_summaries(results):
    if not results:
        print("No matches.")
        return
    for c in results:
        score = c.get("trust_score")
        score_s = f"{score:>3}/100" if score is not None else "   -   "
        print(f"{score_s}  {c.get('country_code','--')}  {c.get('name','')}  "
              f"[{c.get('slug','')}]  revenue {_money(c.get('annual_revenue'))}")


def _print_charity(d):
    print(d.get("name", ""))
    print("=" * len(d.get("name", "")))
    reg = d.get("registration_number") or d.get("ein") or d.get("uk_charity_number") or "-"
    print(f"Country: {d.get('country_code')}   Registration: {reg}   Category: {d.get('category') or '-'}")
    print(f"Integrity score: {d.get('trust_score') if d.get('trust_score') is not None else '-'}/100   "
          f"Data completeness: {d.get('data_completeness') if d.get('data_completeness') is not None else '-'}%")
    print(f"Revenue: {_money(d.get('annual_revenue'))}   Expenses: {_money(d.get('annual_expenses'))}   "
          f"Program spend: {d.get('program_spend_pct') if d.get('program_spend_pct') is not None else '-'}%")
    if d.get("website"):
        print(f"Website: {d['website']}")
    flags = d.get("red_flags") or []
    print(f"Red flags: {len(flags)}" + ("" if not flags else " (" + ", ".join(f.get('flag_type', '') for f in flags) + ")"))
    print(f"Page: https://giveradar.com/charity/{d.get('slug')}/")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="giveradar", description="GiveRadar charity data API client")
    p.add_argument("--key", help="API key (default: GIVERADAR_API_KEY env var)")
    p.add_argument("--json", action="store_true", help="print raw JSON")
    p.add_argument("--version", action="version", version=f"giveradar {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search charities by name or EIN")
    s.add_argument("query"); s.add_argument("--country", help="2-letter ISO code")
    v = sub.add_parser("verify", help="look up by registration number or EIN")
    v.add_argument("number"); v.add_argument("--country", help="2-letter ISO code")
    for name, helptext in (("charity", "full profile by slug"), ("financials", "filings by slug (Pro)"), ("news", "news by slug")):
        sp = sub.add_parser(name, help=helptext); sp.add_argument("slug")
    sub.add_parser("stats", help="platform totals")

    a = p.parse_args(argv)
    gr = Client(api_key=a.key)
    try:
        if a.cmd == "search":
            out = gr.search(a.query, country=a.country)
        elif a.cmd == "verify":
            out = gr.verify(a.number, country=a.country)
        elif a.cmd == "charity":
            out = gr.charity(a.slug)
        elif a.cmd == "financials":
            out = gr.financials(a.slug)
        elif a.cmd == "news":
            out = gr.news(a.slug)
        else:
            out = gr.stats()
    except GiveRadarError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    if a.cmd in ("search", "verify"):
        _print_summaries(out.get("results", []))
    elif a.cmd == "charity":
        _print_charity(out)
    elif a.cmd == "financials":
        for f in out.get("filings", []):
            print(f"{f.get('fiscal_year')}: revenue {_money(f.get('total_revenue'))}  expenses {_money(f.get('total_expenses'))}  programs {_money(f.get('program_expenses'))}")
        sb = out.get("spending_breakdown") or {}
        if sb:
            print(f"Program spend {sb.get('program_spend_pct')}%  admin {sb.get('admin_spend_pct')}%")
    elif a.cmd == "news":
        for art in out.get("articles", []):
            print(f"{(art.get('published_at') or '')[:10]}  {art.get('title','')}  <{art.get('url','')}>")
        print(f"{out.get('article_count', 0)} article(s), average tone {out.get('average_tone')}")
    else:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
