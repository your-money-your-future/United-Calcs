#!/usr/bin/env python3
"""Validate the generated calculator feed and its HTML integration."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "calculators" / "Comparison" / "fund-performance-data.js"
HTML = ROOT / "calculators" / "Comparison" / "Fund Comparison.html"
PREFIX = "window.FUND_PERFORMANCE_DATA = "


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_feed(path: Path = FEED) -> dict:
    text = path.read_text(encoding="utf-8")
    assignment = next((line for line in text.splitlines() if line.startswith(PREFIX)), None)
    require(assignment is not None, "generated feed assignment is missing")
    payload = text[text.index(PREFIX) + len(PREFIX) :].strip()
    require(payload.endswith(";"), "generated feed must end with a semicolon")
    return json.loads(payload[:-1])


def validate(feed: dict, html: str) -> None:
    require(feed.get("schemaVersion") == 1, "unsupported feed schema")
    date.fromisoformat(feed["reportDate"])
    require(len(feed.get("reportSha256", "")) == 64, "report checksum is invalid")

    funds = feed.get("funds", [])
    unavailable = feed.get("unavailableFunds", [])
    require(feed.get("availableFundCount") == len(funds), "available fund count mismatch")
    require(len(funds) + len(unavailable) == feed.get("monitoredFundCount") == 12, "fund coverage mismatch")

    all_ids = [fund["id"] for fund in funds + unavailable]
    require(len(all_ids) == len(set(all_ids)), "duplicate fund id")
    require("cbusTTR" not in all_ids and "cbusRetired" not in all_ids, "retirement or TTR data leaked into feed")

    for fund in funds:
        require(fund.get("options"), f"no options for {fund.get('name')}")
        require(fund.get("effectiveDates"), f"no effective dates for {fund.get('name')}")
        names: set[str] = set()
        for option in fund["options"]:
            require(option["name"] not in names, f"duplicate option for {fund['name']}: {option['name']}")
            names.add(option["name"])
            require(option["periodYears"] in {1, 3, 5, 7, 10}, "invalid annualised period")
            require(-1.0 <= option["rate"] <= 1.0, "return outside validation range")
            date.fromisoformat(option["effectiveDate"])
            require(option["effectiveDate"] in fund["effectiveDates"], "option date missing from fund dates")

    require('src="fund-performance-data.js"' in html, "calculator does not load the generated feed")
    require("window.FUND_PERFORMANCE_DATA" in html, "calculator does not consume the generated feed")
    require("cbusTTR" not in html and "cbusRetired" not in html, "legacy TTR/retirement options remain in calculator")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", type=Path, default=FEED)
    parser.add_argument("--html", type=Path, default=HTML)
    args = parser.parse_args()
    feed = load_feed(args.feed)
    validate(feed, args.html.read_text(encoding="utf-8"))
    option_count = sum(len(fund["options"]) for fund in feed["funds"])
    print(
        f"Fund comparison validation passed: report={feed['reportDate']} "
        f"funds={len(feed['funds'])}/{feed['monitoredFundCount']} options={option_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
