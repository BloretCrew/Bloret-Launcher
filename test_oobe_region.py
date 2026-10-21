import unittest
from pathlib import Path

from modules.countries import (
    country_options,
    is_region_unavailable,
    system_country_code,
)


class CountryDataTests(unittest.TestCase):
    def test_country_list_is_complete_and_unique(self):
        options = country_options("zh-cn")
        self.assertEqual(len(options), 249)
        codes = [item["code"] for item in options]
        self.assertEqual(len(codes), len(set(codes)))
        for item in options:
            self.assertEqual(len(item["code"]), 2)
            self.assertTrue(item["name"].strip())
        for code in ("CN", "US", "HK", "TW"):
            self.assertIn(code, codes)

    def test_country_names_follow_launcher_language(self):
        self.assertEqual(
            next(item["name"] for item in country_options("zh-cn") if item["code"] == "CN"),
            "中国大陆",
        )
        self.assertEqual(
            next(item["name"] for item in country_options("zh-TW") if item["code"] == "CN"),
            "中國大陸",
        )
        self.assertEqual(
            next(item["name"] for item in country_options("en-GB") if item["code"] == "CN"),
            "China",
        )

    def test_system_country_is_a_known_code(self):
        codes = {item["code"] for item in country_options("en-GB")}
        self.assertIn(system_country_code(), codes)

    def test_only_mainland_china_is_unavailable(self):
        self.assertTrue(is_region_unavailable("CN"))
        self.assertTrue(is_region_unavailable("cn"))
        self.assertTrue(is_region_unavailable(" CN "))
        for code in ("US", "HK", "MO", "TW", "", None):
            self.assertFalse(is_region_unavailable(code))


class OobeOverlayTests(unittest.TestCase):
    def test_overlay_has_country_gate_after_language_page(self):
        overlay = Path("qml/OOBEOverlay.qml").read_text(encoding="utf-8")
        self.assertIn("property int totalPages: 8", overlay)
        self.assertIn('Backend.tr("选择国家或地区")', overlay)
        self.assertIn("visible: oobeOverlay.currentPage === 2", overlay)
        self.assertIn("visible: oobeOverlay.currentPage === 3", overlay)
        self.assertIn("function goNext()", overlay)
        self.assertIn("Backend.isRegionUnavailable(oobeOverlay.selectedRegion)", overlay)
        self.assertIn("case 2: return !!oobeOverlay.selectedRegion && !oobeOverlay.regionUnavailable", overlay)
        self.assertIn("case 7: return true", overlay)


if __name__ == "__main__":
    unittest.main()
