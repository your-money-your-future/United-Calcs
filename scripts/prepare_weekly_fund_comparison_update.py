#!/usr/bin/env python3
"""Prepare and validate one verified weekly feed for GitHub PR publication."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-project", type=Path, required=True)
    parser.add_argument("--report-date", required=True)
    parser.add_argument("--output", type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ttr-csv", type=Path)
    source.add_argument("--ttr-html", type=Path)
    parser.add_argument("--ttr-source-url")
    parser.add_argument("--whole-journey-output", type=Path)
    args = parser.parse_args()

    if bool(args.ttr_html) != bool(args.ttr_source_url):
        parser.error("--ttr-html requires --ttr-source-url; CSV must not specify it")
    source_args = (["--ttr-html", str(args.ttr_html.resolve()), "--ttr-source-url", args.ttr_source_url]
                   if args.ttr_html else ["--ttr-csv", str(args.ttr_csv.resolve())])

    if run("git", "status", "--porcelain", capture=True):
        raise SystemExit("refusing to prepare an update from a dirty calculator checkout")
    if run("git", "branch", "--show-current", capture=True) != "main":
        raise SystemExit("refusing to prepare an update unless the calculator checkout is on main")

    run("git", "fetch", "origin", "main")
    run("git", "merge", "--ff-only", "origin/main")
    output = args.output or Path(tempfile.gettempdir()) / f"fund-performance-data-{args.report_date}.js"
    whole_journey_output = args.whole_journey_output or Path(tempfile.gettempdir()) / f"whole-journey-performance-data-{args.report_date}.js"
    run(
        sys.executable,
        "scripts/update_fund_comparison.py",
        "--report-project",
        str(args.report_project.resolve()),
        "--report-date",
        args.report_date,
        "--output",
        str(output),
    )
    run(sys.executable, "scripts/validate_fund_comparison.py", "--feed", str(output))
    run(
        sys.executable,
        "scripts/update_whole_journey.py",
        "--report-project",
        str(args.report_project.resolve()),
        "--report-date",
        args.report_date,
        *source_args,
        "--output",
        str(whole_journey_output),
    )
    run(sys.executable, "scripts/validate_whole_journey.py", "--feed", str(whole_journey_output))
    print(output.resolve())
    print(whole_journey_output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
