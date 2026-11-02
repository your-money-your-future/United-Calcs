from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


update = load_module("update_whole_journey", ROOT / "scripts" / "update_whole_journey.py")
validator = load_module("validate_whole_journey", ROOT / "scripts" / "validate_whole_journey.py")


class WholeJourneyTests(unittest.TestCase):
    def test_ttr_parser_reads_all_options_and_periods(self):
        csv_text = (
            ",1 year (%),3 years p.a (%),5 years p.a (%),7 years p.a (%)\n"
            "Conservative Growth (default),5.46%,7.92%,4.87%,5.38%\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "september-2026-ttr-crediting-rates.csv"
            path.write_text(csv_text, encoding="utf-8")
            rows = update.ttr_rows(path)
        self.assertEqual(rows[0]["effective_date"], "2026-09-30")
        self.assertEqual(rows[0]["seven_year"], 0.0538)

    def test_repository_feed_is_valid(self):
        feed = validator.load_feed()
        html = validator.HTML.read_text(encoding="utf-8")
        validator.validate(feed, html)


if __name__ == "__main__":
    unittest.main()
