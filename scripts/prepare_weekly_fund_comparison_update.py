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
    args = parser.parse_args()

    if run("git", "status", "--porcelain", capture=True):
        raise SystemExit("refusing to prepare an update from a dirty calculator checkout")
    if run("git", "branch", "--show-current", capture=True) != "main":
        raise SystemExit("refusing to prepare an update unless the calculator checkout is on main")

    run("git", "fetch", "origin", "main")
    run("git", "merge", "--ff-only", "origin/main")
    output = args.output or Path(tempfile.gettempdir()) / f"fund-performance-data-{args.report_date}.js"
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
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
