#!/usr/bin/env python3
"""Build the comparison-calculator feed from a verified weekly report run."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "calculators" / "Comparison" / "fund-performance-data.js"

FUND_IDS = {
    "Australian Retirement Trust": "art",
    "AustralianSuper": "ausSuper",
    "Aware Super": "aware",
    "Brighter Super": "brighter",
    "BUSSQ": "bussq",
    "CareSuper": "caresuper",
    "Cbus": "cbus",
    "HESTA": "hesta",
    "Hostplus": "hostplus",
    "MLC MasterKey Fundamentals": "mlc",
    "Rest": "rest",
    "UniSuper": "unisuper",
}

PERIODS = (
    ("ten_year", 10),
    ("seven_year", 7),
    ("five_year", 5),
    ("three_year", 3),
    ("one_year", 1),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(project: Path, manifest: dict[str, Any], report_date: str) -> None:
    require(manifest.get("report_date") == report_date, "manifest report date does not match")
    require(manifest.get("status") == "sent", "report manifest must have status 'sent'")
    require(not manifest.get("test_run", False), "test reports cannot update the calculator")

    validation = manifest.get("validation", {})
    for key in ("all_funds_present", "pdf_render_checked", "visual_inspection_passed"):
        require(validation.get(key) is True, f"manifest validation failed: {key}")

    report_path = project / str(manifest.get("report_path", ""))
    require(report_path.is_file(), "verified report PDF is missing")
    actual_report_sha = sha256(report_path)
    require(actual_report_sha == manifest.get("report_sha256"), "report PDF checksum mismatch")
    require(
        actual_report_sha == validation.get("visual_inspection_sha256"),
        "visual inspection does not cover the current report PDF",
    )

    delivery = manifest.get("delivery_verification", {})
    for key in ("recipient_verified", "subject_verified", "pdf_attachment_verified", "sent_label_verified"):
        require(delivery.get(key) is True, f"delivery verification failed: {key}")


def latest_sent_report_date(project: Path) -> str:
    candidates: list[str] = []
    for path in (project / "state").glob("????-??-??.json"):
        manifest = load_json(path)
        if manifest.get("status") == "sent" and not manifest.get("test_run", False):
            candidates.append(path.stem)
    require(bool(candidates), "no sent production report manifest found")
    return max(candidates)


def longest_return(row: dict[str, Any]) -> tuple[int, float] | None:
    for field, years in PERIODS:
        value = row.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            require(-100.0 <= float(value) <= 100.0, f"implausible return for {row.get('option')}: {value}")
            return years, round(float(value) / 100.0, 8)
    return None


def build_feed(manifest: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    report_date = str(manifest["report_date"])
    require(canonical.get("report_date") == report_date, "canonical report date does not match manifest")

    funds = canonical.get("funds")
    require(isinstance(funds, list), "canonical funds must be a list")
    by_brand = {fund.get("brand"): fund for fund in funds if isinstance(fund, dict)}
    require(set(by_brand) == set(FUND_IDS), "canonical fund universe does not match the configured 12 funds")

    available: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    for brand, fund_id in FUND_IDS.items():
        fund = by_brand[brand]
        if fund.get("source_unavailable"):
            unavailable.append({"id": fund_id, "name": brand, "reason": "Source unavailable in this report"})
            continue

        options: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in fund.get("accumulation", []):
            option_name = str(row.get("option", "")).strip()
            require(option_name and option_name not in seen, f"duplicate or blank option for {brand}: {option_name!r}")
            selected = longest_return(row)
            if selected is None:
                continue
            years, rate = selected
            effective_date = row.get("effective_date")
            require(isinstance(effective_date, str), f"missing effective date for {brand} / {option_name}")
            date.fromisoformat(effective_date)
            seen.add(option_name)
            options.append(
                {
                    "name": option_name,
                    "rate": rate,
                    "periodYears": years,
                    "effectiveDate": effective_date,
                    "basis": row.get("basis") or "Not stated",
                }
            )

        require(options, f"no annualised accumulation returns available for {brand}")
        options.sort(key=lambda item: (item["periodYears"] * -1, item["name"].casefold()))
        effective_dates = sorted({item["effectiveDate"] for item in options})
        available.append(
            {
                "id": fund_id,
                "name": brand,
                "sourceId": fund.get("source_id"),
                "effectiveDates": effective_dates,
                "options": options,
            }
        )

    available.sort(key=lambda item: item["name"].casefold())
    require(len(available) + len(unavailable) == 12, "feed must account for all 12 monitored funds")
    return {
        "schemaVersion": 1,
        "reportDate": report_date,
        "reportSha256": manifest["report_sha256"],
        "methodology": "Cbus-equivalent Net Investment Return; accumulation only; longest available annualised period",
        "availableFundCount": len(available),
        "monitoredFundCount": 12,
        "funds": available,
        "unavailableFunds": unavailable,
    }


def write_feed(feed: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2, ensure_ascii=False, sort_keys=False)
    output.write_text(
        "// Generated by scripts/update_fund_comparison.py; do not edit by hand.\n"
        f"window.FUND_PERFORMANCE_DATA = {payload};\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-project", type=Path, required=True)
    parser.add_argument("--report-date", help="YYYY-MM-DD; defaults to the latest sent production report")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    project = args.report_project.resolve()
    report_date = args.report_date or latest_sent_report_date(project)
    require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", report_date)), "invalid report date")
    datetime.strptime(report_date, "%Y-%m-%d")

    manifest = load_json(project / "state" / f"{report_date}.json")
    canonical = load_json(project / "data" / "runs" / report_date / "canonical.json")
    validate_manifest(project, manifest, report_date)
    feed = build_feed(manifest, canonical)
    write_feed(feed, args.output)
    print(
        f"Updated {args.output} from verified report {report_date}: "
        f"{feed['availableFundCount']}/{feed['monitoredFundCount']} funds available"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
