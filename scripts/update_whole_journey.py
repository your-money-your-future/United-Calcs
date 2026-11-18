#!/usr/bin/env python3
"""Build the Whole Journey Cbus return feed from a verified weekly report."""

from __future__ import annotations

import argparse
import csv
import calendar
from html.parser import HTMLParser
from urllib.parse import urlparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "calculators" / "The Whole Journey" / "whole-journey-performance-data.js"
PERIODS = (
    ("ten_year", 10),
    ("seven_year", 7),
    ("five_year", 5),
    ("three_year", 3),
    ("one_year", 1),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    report_sha = sha256(report_path)
    require(report_sha == manifest.get("report_sha256"), "report PDF checksum mismatch")
    require(report_sha == validation.get("visual_inspection_sha256"), "visual inspection does not cover current PDF")
    delivery = manifest.get("delivery_verification", {})
    for key in ("recipient_verified", "subject_verified", "pdf_attachment_verified", "sent_label_verified"):
        require(delivery.get(key) is True, f"delivery verification failed: {key}")


def normalise_option(name: str) -> str:
    return name.replace("**", "").replace("^", "").strip()


def parse_percent(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.casefold() in {"n/a", "na", "-", "—"}:
        return None
    number = float(text)
    require(-100.0 <= number <= 100.0, f"implausible return: {value}")
    return round(number / 100.0, 8)


def ttr_rows(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f"TTR source file not found: {path}")
    match = re.search(r"([A-Za-z]+)-(\d{4})-ttr-crediting-rates\.csv$", path.name, re.IGNORECASE)
    require(match is not None, "TTR filename must identify its effective month")
    month = datetime.strptime(f"{match.group(1)} {match.group(2)}", "%B %Y")
    if month.month == 12:
        effective_date = date(month.year, 12, 31)
    else:
        effective_date = date(month.year, month.month + 1, 1).fromordinal(
            date(month.year, month.month + 1, 1).toordinal() - 1
        )
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for item in csv.DictReader(handle):
            name = normalise_option(item.get("") or "")
            if not name:
                continue
            rows.append(
                {
                    "option": name,
                    "effective_date": effective_date.isoformat(),
                    "basis": "Published",
                    "ten_year": parse_percent(item.get("10 years p.a (%)") or item.get("10 years p.a. (%)")),
                    "seven_year": parse_percent(item.get("7 years p.a. (%)") or item.get("7 years p.a (%)")),
                    "five_year": parse_percent(item.get("5 years p.a. (%)") or item.get("5 years p.a (%)")),
                    "three_year": parse_percent(item.get("3 years p.a. (%)") or item.get("3 years p.a (%)")),
                    "one_year": parse_percent(item.get("1 year (%)")),
                }
            )
    require(rows, "TTR source contained no options")
    return rows


class TTRTableParser(HTMLParser):
    """Read only the monthly table beneath the exact TTR heading."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = None
        self.active = False
        self.matches = 0
        self.paragraph = None
        self.paragraphs = []
        self.in_table = False
        self.tables = []
        self.table = []
        self.row = []
        self.cell = None
        self.sup_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "sup":
            self.sup_depth += 1
        if tag == "h2":
            self.active = False
            self.heading = []
        elif self.active:
            if tag == "p" and not self.tables and not self.in_table:
                self.paragraph = []
            elif tag == "table":
                require(not self.in_table, "nested TTR tables are not supported")
                self.in_table = True
                self.table = []
            elif self.in_table and tag == "tr":
                self.row = []
            elif self.in_table and tag in {"th", "td"}:
                self.cell = []

    def handle_data(self, data):
        if self.sup_depth:
            return
        for target in (self.heading, self.paragraph, self.cell):
            if target is not None:
                target.append(data)

    def handle_endtag(self, tag):
        if tag == "sup":
            self.sup_depth = max(0, self.sup_depth - 1)
        elif tag == "h2" and self.heading is not None:
            self.active = " ".join("".join(self.heading).split()) == "Transition to Retirement investment performance"
            self.matches += int(self.active)
            self.heading = None
        elif self.active:
            if tag == "p" and self.paragraph is not None:
                self.paragraphs.append(" ".join("".join(self.paragraph).split()))
                self.paragraph = None
            elif self.in_table and tag in {"th", "td"} and self.cell is not None:
                self.row.append(" ".join("".join(self.cell).split()))
                self.cell = None
            elif self.in_table and tag == "tr":
                self.table.append(self.row)
            elif tag == "table" and self.in_table:
                self.tables.append(self.table)
                self.in_table = False


def ttr_html_rows(path: Path, source_url: str) -> list[dict[str, Any]]:
    url = urlparse(source_url)
    require(url.scheme == "https" and url.hostname in {"cbussuper.com.au", "www.cbussuper.com.au"}
            and url.path.rstrip("/") == "/investments/investment-performance"
            and not url.username and not url.password and url.port in {None, 443},
            "TTR HTML must come from the official Cbus investment performance page")
    parser = TTRTableParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    require(parser.matches == 1 and len(parser.tables) == 1, "expected exactly one TTR heading and monthly table")
    dates = [re.fullmatch(r"To\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})", text) for text in parser.paragraphs]
    dates = [match for match in dates if match]
    require(len(dates) == 1, "TTR monthly reference date missing or ambiguous")
    effective_date = datetime.strptime(dates[0].group(1), "%d %B %Y").date()
    require(effective_date.day == calendar.monthrange(effective_date.year, effective_date.month)[1],
            "TTR reference date must be month end")
    table = parser.tables[0]
    require(len(table) == 12, "TTR monthly table must contain exactly 11 options")
    headers = table[0]
    require(len(headers) in {7, 8} and not headers[0], "unexpected TTR table schema")
    columns = {}
    ignored = set()
    for index, header in enumerate(headers[1:], 1):
        normalised = re.sub(r"[().%\s]", "", header).lower()
        if normalised in {"1month", "financialyeartodate"}:
            require(normalised not in ignored, "duplicate TTR column")
            ignored.add(normalised)
            continue
        match = re.fullmatch(r"(1year|(?:3|5|7|10)yearspa)", normalised)
        require(match is not None, f"unrecognised TTR column: {header}")
        years = int(re.match(r"\d+", normalised).group())
        require(years not in columns, "duplicate TTR annualised column")
        columns[years] = index
    require(set(columns) in ({1, 3, 5, 7}, {1, 3, 5, 7, 10})
            and ignored == {"1month", "financialyeartodate"}, "missing TTR columns")
    rows = []
    for values in table[1:]:
        require(len(values) == len(headers), "malformed TTR row")
        row = {"option": normalise_option(values[0]), "effective_date": effective_date.isoformat(), "basis": "Published"}
        for field, years in PERIODS:
            row[field] = parse_percent(values[columns[years]]) if years in columns else None
        rows.append(row)
    phase_payload(rows, values_are_percent=False)  # Reject duplicates, blank names and missing returns.
    return rows


def phase_payload(rows: list[dict[str, Any]], *, values_are_percent: bool) -> dict[str, Any]:
    options: list[dict[str, Any]] = []
    names: set[str] = set()
    for row in rows:
        name = normalise_option(str(row.get("option", "")))
        require(name and name not in names, f"duplicate or blank option: {name!r}")
        effective_date = row.get("effective_date")
        require(isinstance(effective_date, str), f"missing effective date for {name}")
        date.fromisoformat(effective_date)
        returns: list[dict[str, Any]] = []
        for field, years in PERIODS:
            value = row.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rate = round(float(value) / 100.0, 8) if values_are_percent else round(float(value), 8)
                require(-1.0 <= rate <= 1.0, f"return outside validation range for {name}")
                returns.append({"periodYears": years, "rate": rate})
        require(returns, f"no annualised returns available for {name}")
        names.add(name)
        options.append(
            {
                "name": name,
                "effectiveDate": effective_date,
                "basis": row.get("basis") or "Not stated",
                "returns": returns,
            }
        )
    return {
        "effectiveDates": sorted({option["effectiveDate"] for option in options}),
        "options": options,
    }


def build_feed(manifest: dict[str, Any], canonical: dict[str, Any], ttr_source: Path, *, ttr_source_url: str | None = None) -> dict[str, Any]:
    report_date = str(manifest["report_date"])
    require(canonical.get("report_date") == report_date, "canonical report date does not match manifest")
    funds = canonical.get("funds")
    require(isinstance(funds, list), "canonical funds must be a list")
    cbus_matches = [fund for fund in funds if isinstance(fund, dict) and fund.get("brand") == "Cbus"]
    require(len(cbus_matches) == 1, "canonical report must contain exactly one Cbus record")
    cbus = cbus_matches[0]
    require(not cbus.get("source_unavailable"), "Cbus source is unavailable in this report")
    accumulation = phase_payload(cbus.get("accumulation", []), values_are_percent=True)
    retired = phase_payload(cbus.get("retirement", []), values_are_percent=True)
    ttr = phase_payload(ttr_html_rows(ttr_source, ttr_source_url) if ttr_source_url else ttr_rows(ttr_source), values_are_percent=False)
    require(
        set(accumulation["effectiveDates"]) == set(retired["effectiveDates"]) == set(ttr["effectiveDates"]),
        "Cbus accumulation, TTR and fully retired source months do not match",
    )
    require(len(accumulation["options"]) == len(ttr["options"]) == len(retired["options"]) == 11, "each phase must contain 11 Cbus options")
    return {
        "schemaVersion": 1,
        "reportDate": report_date,
        "reportSha256": manifest["report_sha256"],
        "fund": "Cbus",
        "sourceId": cbus.get("source_id"),
        "ttrSourceSha256": sha256(ttr_source),
        **({"ttrSourceUrl": ttr_source_url, "ttrSourceFormat": "html"} if ttr_source_url else {}),
        "methodology": "Published Cbus crediting rates; all available annualised periods; phases kept separate",
        "phases": {"accumulation": accumulation, "ttr": ttr, "retired": retired},
    }


def write_feed(feed: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(feed, indent=2, ensure_ascii=False)
    output.write_text(
        "// Generated by scripts/update_whole_journey.py; do not edit by hand.\n"
        f"window.WHOLE_JOURNEY_PERFORMANCE_DATA = {payload};\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-project", type=Path, required=True)
    parser.add_argument("--report-date", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ttr-csv", type=Path)
    source.add_argument("--ttr-html", type=Path)
    parser.add_argument("--ttr-source-url")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.report_date)), "invalid report date")
    project = args.report_project.resolve()
    manifest = load_json(project / "state" / f"{args.report_date}.json")
    canonical = load_json(project / "data" / "runs" / args.report_date / "canonical.json")
    validate_manifest(project, manifest, args.report_date)
    require(bool(args.ttr_html) == bool(args.ttr_source_url), "--ttr-html requires --ttr-source-url; CSV must not specify it")
    feed = build_feed(manifest, canonical, (args.ttr_html or args.ttr_csv).resolve(), ttr_source_url=args.ttr_source_url)
    write_feed(feed, args.output)
    print(f"Updated {args.output} from verified report {args.report_date}: 3 Cbus phases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
