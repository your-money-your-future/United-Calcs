#!/usr/bin/env python3
"""Validate the generated Whole Journey performance feed and integration."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "calculators" / "The Whole Journey" / "whole-journey-performance-data.js"
HTML = ROOT / "calculators" / "The Whole Journey" / "Superannuation Lifetime Projection.html"
PREFIX = "window.WHOLE_JOURNEY_PERFORMANCE_DATA = "


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_feed(path: Path = FEED) -> dict:
    text = path.read_text(encoding="utf-8")
    require(PREFIX in text, "generated feed assignment is missing")
    payload = text[text.index(PREFIX) + len(PREFIX) :].strip()
    require(payload.endswith(";"), "generated feed must end with a semicolon")
    return json.loads(payload[:-1])


def validate(feed: dict, html: str) -> None:
    require(feed.get("schemaVersion") == 1, "unsupported feed schema")
    date.fromisoformat(feed["reportDate"])
    require(len(feed.get("reportSha256", "")) == 64, "report checksum is invalid")
    require(len(feed.get("ttrSourceSha256", "")) == 64, "TTR source checksum is invalid")
    require(feed.get("fund") == "Cbus", "Whole Journey feed must contain Cbus data")
    phases = feed.get("phases", {})
    require(set(phases) == {"accumulation", "ttr", "retired"}, "feed must contain exactly three phases")
    for phase_name, phase in phases.items():
        require(len(phase.get("options", [])) == 11, f"{phase_name} must contain 11 options")
        require(phase.get("effectiveDates"), f"{phase_name} effective dates are missing")
        names: set[str] = set()
        for option in phase["options"]:
            require(option["name"] not in names, f"duplicate {phase_name} option: {option['name']}")
            names.add(option["name"])
            date.fromisoformat(option["effectiveDate"])
            require(option["effectiveDate"] in phase["effectiveDates"], "option date missing from phase dates")
            require(option.get("returns"), f"{phase_name} / {option['name']} has no annualised returns")
            periods: set[int] = set()
            for item in option["returns"]:
                require(item["periodYears"] in {1, 3, 5, 7, 10}, "invalid annualised period")
                require(item["periodYears"] not in periods, "duplicate annualised period")
                periods.add(item["periodYears"])
                require(-1.0 <= item["rate"] <= 1.0, "return outside validation range")
    require('src="whole-journey-performance-data.js"' in html, "calculator does not load the generated feed")
    require("window.WHOLE_JOURNEY_PERFORMANCE_DATA" in html, "calculator does not consume the generated feed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", type=Path, default=FEED)
    parser.add_argument("--html", type=Path, default=HTML)
    args = parser.parse_args()
    feed = load_feed(args.feed)
    validate(feed, args.html.read_text(encoding="utf-8"))
    count = sum(len(phase["options"]) for phase in feed["phases"].values())
    print(f"Whole Journey validation passed: report={feed['reportDate']} phases=3 options={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
