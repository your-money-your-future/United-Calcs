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

    def html_source(self, *, date="31 October 2026", count=11, value="4.40%", heading="Transition to Retirement investment performance"):
        headers = ["", "1 month (%)", "Financial Year to Date (%)", "1 year (%)", "3 years p.a (%)", "5 years p.a (%)", "7 years p.a (%)"]
        table = "<table><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
        for index in range(count):
            values = [f"Option {index}", "0.10%", "0.80%", value, "8.25%", "n/a", "5.32%"]
            table += "<tr>" + "".join(f"<td>{v}</td>" for v in values) + "</tr>"
        return f"<h2>Super investment performance</h2><p>To 30 June 2026</p><table></table><h2>{heading}</h2><p>To {date}<sup>2</sup></p>{table}</table><h2>Fully Retired investment performance</h2><p>To 30 June 2026</p><table></table>"

    def parse_html(self, content, url="https://www.cbussuper.com.au/investments/investment-performance"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "performance.html"
            path.write_text(content)
            return update.ttr_html_rows(path, url)

    def test_html_selects_ttr_date_and_periods_without_inventing_ten_year(self):
        rows = self.parse_html(self.html_source())
        self.assertEqual(len(rows), 11)
        self.assertEqual(rows[0]["effective_date"], "2026-10-31")
        self.assertEqual(rows[0]["one_year"], 0.044)
        self.assertEqual(rows[0]["seven_year"], 0.0532)
        self.assertIsNone(rows[0]["five_year"])
        self.assertIsNone(rows[0]["ten_year"])

    def test_html_rejects_wrong_source(self):
        with self.assertRaisesRegex(ValueError, "official Cbus"):
            self.parse_html(self.html_source(), "https://cbussuper.com.au.example.org/investments/investment-performance")

    def test_html_rejects_incomplete_or_ambiguous_source(self):
        valid = self.html_source()
        for content in [self.html_source(count=10), self.html_source(heading="Fully Retired investment performance"),
                        valid + valid, valid.replace("Option 1<", "Option 0<"),
                        valid.replace("7 years p.a (%)", "Since inception (%)"),
                        self.html_source(date="30 October 2026"), self.html_source(value="NaN"),
                        self.html_source(value="not disclosed")]:
            with self.subTest(content=content[:60]), self.assertRaises(ValueError):
                self.parse_html(content)

    def test_html_rejects_mismatched_phase_months(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "performance.html"
            path.write_text(self.html_source())
            row = {"option": "Growth", "effective_date": "2026-09-30", "one_year": 5.0}
            canonical = {"report_date": "2026-11-17", "funds": [{"brand": "Cbus", "accumulation": [row], "retirement": [row]}]}
            with self.assertRaisesRegex(ValueError, "months do not match"):
                update.build_feed({"report_date": "2026-11-17"}, canonical, path,
                                  ttr_source_url="https://www.cbussuper.com.au/investments/investment-performance")

    def test_repository_feed_is_valid(self):
        feed = validator.load_feed()
        html = validator.HTML.read_text(encoding="utf-8")
        validator.validate(feed, html)


if __name__ == "__main__":
    unittest.main()
