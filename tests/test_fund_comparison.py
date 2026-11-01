from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


update = load_module("update_fund_comparison", ROOT / "scripts" / "update_fund_comparison.py")
validator = load_module("validate_fund_comparison", ROOT / "scripts" / "validate_fund_comparison.py")


class FundComparisonTests(unittest.TestCase):
    def test_longest_return_prefers_ten_year(self):
        years, rate = update.longest_return({"option": "Growth", "ten_year": 8.5, "five_year": 10.2})
        self.assertEqual(years, 10)
        self.assertEqual(rate, 0.085)

    def test_longest_return_falls_back_in_defined_order(self):
        years, rate = update.longest_return({"option": "Growth", "ten_year": None, "seven_year": None, "five_year": 7.25})
        self.assertEqual(years, 5)
        self.assertEqual(rate, 0.0725)

    def test_repository_feed_is_valid(self):
        feed = validator.load_feed()
        html = validator.HTML.read_text(encoding="utf-8")
        validator.validate(feed, html)


if __name__ == "__main__":
    unittest.main()
